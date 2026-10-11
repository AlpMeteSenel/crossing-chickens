"""Set NCNN CPU threads at construction time, before model weights are loaded."""
from contextlib import contextmanager

@contextmanager
def ncnn_threads(count=2):
    import ncnn
    factory=ncnn.Net
    def configured():
        net=factory();net.opt.num_threads=count;return net
    ncnn.Net=configured
    try:yield
    finally:ncnn.Net=factory
