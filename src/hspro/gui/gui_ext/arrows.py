from abc import abstractmethod
from enum import Enum, auto

# from .. import functions as fn
# from ..Qt import QtGui, QtWidgets

from math import hypot

# from ..Qt import QtGui, QtWidgets

__all__ = ['XArrowItem']

from pyqtgraph import mkBrush, mkPen
from pyqtgraph.Qt import QtWidgets, QtGui


class XArrowDirection(Enum):
    LEFT = auto()
    RIGHT = auto()
    UP = auto()
    DOWN = auto()


class XArrowItem(QtWidgets.QGraphicsPathItem):
    """
    For displaying scale-invariant arrows.
    For arrows pointing to a location on a curve, see CurveArrow

    """

    def __init__(self, parent=None, **opts):
        """
        Arrows can be initialized with any keyword arguments accepted by
        the setStyle() method.
        """
        self.opts = {}
        QtWidgets.QGraphicsPathItem.__init__(self, parent)

        if 'size' in opts:
            opts['headLen'] = opts['size']
        if 'width' in opts:
            opts['headWidth'] = opts['width']
        pos = opts.pop('pos', (0, 0))

        defaultOpts = {
            'pxMode': True,
            'angle': -150,  ## If the angle is 0, the arrow points left
            'headLen': 20,
            'headWidth': None,
            'tipAngle': 25,
            'baseAngle': 0,
            'tailLen': None,
            'tailWidth': 3,
            'pen': (200, 200, 200),
            'brush': (50, 50, 200),
        }
        defaultOpts.update(opts)

        self.setStyle(**defaultOpts)

        # for backward compatibility
        self.setPos(*pos)

    @abstractmethod
    def direction(self) -> XArrowDirection:
        pass

    def setStyle(self, **opts):
        """
        Changes the appearance of the arrow.
        All arguments are optional:

        ======================  =================================================
        **Keyword Arguments:**
        angle                   Orientation of the arrow in degrees. Default is
                                0; arrow pointing to the left.
        headLen                 Length of the arrow head, from tip to base.
                                default=20
        headWidth               Width of the arrow head at its base. If
                                headWidth is specified, it overrides tipAngle.
        tipAngle                Angle of the tip of the arrow in degrees. Smaller
                                values make a 'sharper' arrow. default=25
        baseAngle               Angle of the base of the arrow head. Default is
                                0, which means that the base of the arrow head
                                is perpendicular to the arrow tail.
        tailLen                 Length of the arrow tail, measured from the base
                                of the arrow head to the end of the tail. If
                                this value is None, no tail will be drawn.
                                default=None
        tailWidth               Width of the tail. default=3
        pen                     The pen used to draw the outline of the arrow.
        brush                   The brush used to fill the arrow.
        pxMode                  If True, then the arrow is drawn as a fixed size
                                regardless of the scale of its parents (including
                                the ViewBox zoom level).
        ======================  =================================================
        """
        arrowOpts = ['headLen', 'tipAngle', 'baseAngle', 'tailLen', 'tailWidth', 'headWidth']
        allowedOpts = ['angle', 'pen', 'brush', 'pxMode'] + arrowOpts
        needUpdate = False
        for k, v in opts.items():
            if k not in allowedOpts:
                raise KeyError('Invalid arrow style option "%s"' % k)
            if self.opts.get(k) != v:
                needUpdate = True
            self.opts[k] = v

        if not needUpdate:
            return

        opt = dict([(k, self.opts[k]) for k in arrowOpts if k in self.opts])
        tr = QtGui.QTransform()
        tr.rotate(self.opts['angle'])
        self.path = makeXArrowPath(self.direction())
        # down_path = makeArrowPath(**opt)
        # self.path = tr.map(fn.makeArrowPath(**opt))
        # self.path = tr.map(down_path)

        self.setPath(self.path)

        self.setPen(mkPen(self.opts['pen']))
        self.setBrush(mkBrush(self.opts['brush']))

        if self.opts['pxMode']:
            self.setFlags(self.flags() | self.GraphicsItemFlag.ItemIgnoresTransformations)
        else:
            self.setFlags(self.flags() & ~self.GraphicsItemFlag.ItemIgnoresTransformations)

    def paint(self, p, *args):
        p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        super().paint(p, *args)

        # p.setPen(fn.mkPen('r'))
        # p.setBrush(fn.mkBrush(None))
        # p.drawRect(self.boundingRect())

    def shape(self):
        # if not self.opts['pxMode']:
        # return QtWidgets.QGraphicsPathItem.shape(self)
        return self.path

    ## dataBounds and pixelPadding methods are provided to ensure ViewBox can
    ## properly auto-range
    def dataBounds(self, ax, frac, orthoRange=None):
        pw = 0
        pen = self.pen()
        if not pen.isCosmetic():
            pw = pen.width() * 0.7072
        if self.opts['pxMode']:
            return [0, 0]
        else:
            br = self.boundingRect()
            if ax == 0:
                return [br.left() - pw, br.right() + pw]
            else:
                return [br.top() - pw, br.bottom() + pw]

    def pixelPadding(self):
        pad = 0
        if self.opts['pxMode']:
            br = self.boundingRect()
            pad += hypot(br.width(), br.height())
        pen = self.pen()
        if pen.isCosmetic():
            pad += max(1, pen.width()) * 0.7072
        return pad


class XArrowDown(XArrowItem):
    def direction(self) -> XArrowDirection:
        return XArrowDirection.DOWN


class XArrowUp(XArrowItem):
    def direction(self) -> XArrowDirection:
        return XArrowDirection.UP


class XArrowLeft(XArrowItem):
    def direction(self) -> XArrowDirection:
        return XArrowDirection.LEFT


class XArrowRight(XArrowItem):
    def direction(self) -> XArrowDirection:
        return XArrowDirection.RIGHT


def makeXArrowPath(direction: XArrowDirection) -> QtGui.QPainterPath:
    path = QtGui.QPainterPath()
    match direction:
        case XArrowDirection.DOWN:
            path.moveTo(-10, 0)
            path.lineTo(10, 0)
            path.lineTo(0, 15)
            path.lineTo(-10, 0)
        case XArrowDirection.UP:
            path.moveTo(-10, 0)
            path.lineTo(10, 0)
            path.lineTo(0, -15)
            path.lineTo(-10, 0)
        case XArrowDirection.LEFT:
            path.moveTo(0, -10)
            path.lineTo(0, 10)
            path.lineTo(-15, 0)
            path.lineTo(0, -10)
        case XArrowDirection.RIGHT:
            path.moveTo(0, -10)
            path.lineTo(0, 10)
            path.lineTo(15, 0)
            path.lineTo(0, -10)
    return path
