import time

import pika
from loguru import logger
from pika import BlockingConnection
from pika.adapters.blocking_connection import BlockingChannel
from pika.exceptions import AMQPConnectionError, ConnectionClosedByBroker
from pika.spec import Basic, BasicProperties

from src.browser import ChromeBrowserWorker
from src.config import get_connection_parameters
from src.render_worker import RenderWorker


class RenderServer:
    """
    小镜 Bot 渲染服务器
    """

    connection: BlockingConnection
    channel: BlockingChannel
    worker: RenderWorker

    def __init__(self):
        self.init_worker()

    def connect(self):
        """
        创建与 RabbitMQ 的连接和通道，并声明队列。
        """
        while True:
            try:
                self.connection = pika.BlockingConnection(get_connection_parameters())
                self.channel = self.connection.channel()
                self.channel.queue_declare(
                    queue="render",
                    arguments={
                        "x-dead-letter-exchange": "dlx",
                        "x-message-ttl": 60000,
                    },
                )
                self.channel.queue_declare(queue="render_dlx")
                logger.info(" [x] 正在连接至 RabbitMQ 服务器")
                break
            except AMQPConnectionError as e:
                logger.error(f" [!] 连接失败，五秒后重试")
                logger.exception(e)
                time.sleep(5)  # 等待 5 秒后重试连接

    def init_worker(self):
        self.worker = ChromeBrowserWorker()
        self.worker.init()

    def callback(
        self,
        ch: BlockingChannel,
        method: Basic.Deliver,
        properties: BasicProperties,
        body: bytes,
    ):
        """
        回调函数：处理从 'render' 队列中接收到的渲染请求。
        """
        logger.info(f" [x] 接收到了 {body}")
        try:
            img = self.worker.render(body.decode())
        except Exception as e:
            logger.error(f" [!] 渲染失败")
            logger.exception(e)
            ch.basic_nack(delivery_tag=method.delivery_tag or 0, requeue=True)
            if not self.worker.ok:
                self.init_worker()
            return

        ch.basic_ack(delivery_tag=method.delivery_tag or 0)

        ch.basic_publish(
            exchange="",
            routing_key=properties.reply_to or "",
            properties=pika.BasicProperties(
                correlation_id=properties.correlation_id,
            ),
            body=img,
        )
        logger.info(f" [x] 给 correlation_id 以答复: {properties.correlation_id}")

    def start_server(self):
        """
        开始服务器，监听 'render' 队列并处理客户端的渲染请求。
        """
        while True:
            try:
                # 连接到 RabbitMQ
                self.connect()

                # 开始监听 'render' 队列
                self.channel.basic_consume(
                    queue="render", on_message_callback=self.callback
                )
                logger.info(" [x] 开始接收渲染请求")
                self.channel.start_consuming()

            except (AMQPConnectionError, ConnectionClosedByBroker) as e:
                logger.error(f" [!] 连接已丢失，五秒后重置")
                logger.exception(e)
                time.sleep(5)  # 等待 5 秒后重连

            except Exception as e:
                logger.error(" [!] 未知错误发送")
                logger.exception(e)
                break  # 其他未预期的错误，停止服务器
