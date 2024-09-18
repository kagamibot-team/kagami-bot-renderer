import time
from abc import ABC, abstractmethod

from loguru import logger

TEMP = {"work_id": 0}


def get_next_work_id() -> str:
    TEMP["work_id"] += 1
    return "#" + str(TEMP["work_id"])


class RenderWorker(ABC):
    """
    # RenderWorker

    `RenderWorker` 是渲染器的基类。渲染器用于将网页渲染为图片。

    ## 需要继承

    ### `_render` 方法

    渲染的核心逻辑，以及一些错误处理。
    如果是可以被挽回的渲染错误，请在捕捉到错误后将错误包装为
    `KagamiRenderWarning` 并重新抛出。例如：

    ```python
    try:
        ...
    except WebDriverException as e:
        raise KagamiRenderWarning(e)
    ```

    ### `_ok` 方法

    用于获取当前工作者的状态。True 代表当前工作正常

    ### `_init` 方法

    用于初始化当前工作者，例如，启动一个新的浏览器。

    ### `_quit` 方法

    尝试退出当前会话，例如，关闭浏览器等。该方法应该尽可能避免抛出错误。
    例如，浏览器已经关闭时，不应该抛出错误，而是跳过关闭流程。
    """

    worker_id: str
    last_render_begin: float
    started: bool
    exited: bool

    def __init__(self) -> None:
        self.worker_id = get_next_work_id()
        self.last_render_begin = 0
        self.started = False
        self.exited = False

    @abstractmethod
    def _render(self, link: str) -> bytes: ...

    def render(self, link: str) -> bytes:
        self.last_render_begin = time.time()
        logger.info(f"渲染器开始渲染 Worker={self} Link={link}")
        result = self._render(link)
        logger.info(f"渲染器渲染结束 Worker={self} Link={link}")
        return result

    @abstractmethod
    def _ok(self) -> bool: ...

    @property
    def ok(self) -> bool:
        return (self._ok() or not self.started) and not self.exited

    @abstractmethod
    def _init(self): ...

    def init(self) -> None:
        try:
            logger.info(f"渲染器开始启动 Worker={self}")
            self._init()
            logger.info(f"渲染器启动成功 Worker={self}")
        finally:
            self.started = True

    @abstractmethod
    def _quit(self): ...

    def quit(self) -> None:
        if self.exited:
            logger.warning(
                "渲染器已经是正在退出的状态了，但是退出方法被重复调用。"
                f"此时仍然会尝试退出 Worker={self}"
            )
        else:
            logger.info(f"渲染器正在退出 Worker={self}")
        self._quit()
        self.exited = True
        logger.info(f"渲染器退出了 Worker={self}")

    def __str__(self) -> str:
        return f"[{self.__class__.__name__} {self.worker_id}]"

    def __del__(self) -> None:
        if not self.exited:
            logger.warning(f"是不是忘记回收渲染器了？没关系，我帮你关！ Worker={self}")
            self.quit()
