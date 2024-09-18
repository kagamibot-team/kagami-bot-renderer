import pika
from loguru import logger
from pika.adapters.blocking_connection import BlockingChannel
from pika.spec import Basic, BasicProperties

from src.config import get_connection_parameters

from .browser import ChromeBrowserWorker


class RenderServer:
    """
    小镜 Bot 渲染服务器
    """

    def __init__(self):
        self.connection = pika.BlockingConnection(get_connection_parameters())
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue="render")

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
        logger.info(f" [x] Received {body}")
        try:
            img = self.worker.render(body.decode())
        except Exception as e:
            logger.error(f" [!] Render failed")
            logger.exception(e)
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
        logger.info(
            f" [x] Sent render result for correlation_id: {properties.correlation_id}"
        )

    def start_server(self):
        """
        开始服务器，监听 'render' 队列并处理客户端的渲染请求。
        """
        self.channel.basic_consume(queue="render", on_message_callback=self.callback)
        logger.info(" [x] Awaiting RPC requests...")
        self.channel.start_consuming()
