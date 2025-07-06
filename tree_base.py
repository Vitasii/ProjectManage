from PyQt5.QtWidgets import QGraphicsRectItem, QGraphicsTextItem, QGraphicsLineItem, QGraphicsView
from PyQt5.QtGui import QBrush, QColor, QPen, QFont
from PyQt5.QtCore import Qt, QPointF

class NodeItem(QGraphicsRectItem):
    PADDING = 16

    def __init__(self, node_data, color, text, parent=None):
        x, y = node_data.get("pos", [0, 0])
        font = QFont()
        font.setPointSize(10)
        font.setBold(True)
        temp_text = QGraphicsTextItem(text)
        temp_text.setFont(font)
        rect = temp_text.boundingRect()
        width = rect.width() + self.PADDING
        height = rect.height() + self.PADDING
        super().__init__(-width/2, -height/2, width, height)
        self.setPos(x, y)
        self.setBrush(QBrush(QColor(color)))
        self.setPen(QPen(Qt.black, 2))
        self.setZValue(1)
        self.setFlag(QGraphicsRectItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsRectItem.ItemIsMovable, True)
        self.setFlag(QGraphicsRectItem.ItemSendsGeometryChanges, True)
        self.node_data = node_data

        # 文字居中
        self.text = QGraphicsTextItem(text, self)
        self.text.setFont(font)
        self.text.setDefaultTextColor(Qt.black)
        text_rect = self.text.boundingRect()
        self.text.setPos(
            (self.rect().width() - text_rect.width()) / 2 - self.rect().width()/2,
            (self.rect().height() - text_rect.height()) / 2 - self.rect().height()/2
        )
        self.edges = []

    def center(self):
        # 返回场景坐标下的中心点
        return self.mapToScene(QPointF(0, 0))

    def add_edge(self, edge):
        self.edges.append(edge)

    def itemChange(self, change, value):
        if change == QGraphicsRectItem.ItemPositionChange:
            for edge in self.edges:
                edge.update_position()
        return super().itemChange(change, value)

class EdgeLine(QGraphicsLineItem):
    def __init__(self, node1, node2):
        super().__init__()
        self.node1 = node1
        self.node2 = node2
        self.setPen(QPen(Qt.gray, 2))
        self.node1.add_edge(self)
        self.node2.add_edge(self)
        self.update_position()

    def update_position(self):
        p1 = self.node1.center()
        p2 = self.node2.center()
        self.setLine(p1.x(), p1.y(), p2.x(), p2.y())

class ZoomableGraphicsView(QGraphicsView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)

    def wheelEvent(self, event):
        zoomInFactor = 1.15
        zoomOutFactor = 1 / zoomInFactor
        if event.angleDelta().y() > 0:
            self.scale(zoomInFactor, zoomInFactor)
        else:
            self.scale(zoomOutFactor, zoomOutFactor)