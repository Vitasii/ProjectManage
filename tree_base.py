from PyQt5.QtWidgets import QGraphicsRectItem, QGraphicsTextItem, QGraphicsLineItem
from PyQt5.QtGui import QBrush, QColor, QPen, QFont, QPainter
from PyQt5.QtCore import Qt

class NodeItem(QGraphicsRectItem):
    WIDTH = 120
    HEIGHT = 60

    def __init__(self, node_data, color, parent=None):
        x, y = node_data.get("pos", [0, 0])
        super().__init__(x - self.WIDTH/2, y - self.HEIGHT/2, self.WIDTH, self.HEIGHT)
        self.setBrush(QBrush(QColor(color)))
        self.setPen(QPen(Qt.black, 2))
        self.setZValue(1)  # 保证节点在连线之上
        self.setFlag(QGraphicsRectItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsRectItem.ItemIsMovable, True)
        self.node_data = node_data
        self.text = QGraphicsTextItem(self.node_text(), self)
        self.text.setFont(QFont())
        self.text.setDefaultTextColor(Qt.black)
        self.text.setPos(self.rect().center().x() - self.text.boundingRect().width()/2,
                         self.rect().center().y() - self.text.boundingRect().height()/2)
        self.lines = []
        self.parent = parent

    def node_text(self):
        return self.node_data["name"]

    def paint(self, painter, option, widget):
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(self.brush())
        painter.setPen(self.pen())
        painter.drawRoundedRect(self.rect(), 20, 20)
        super().paint(painter, option, widget)

    def mouseReleaseEvent(self, event):
        pos = self.scenePos() + self.rect().center()
        self.node_data["pos"] = [pos.x(), pos.y()]
        self.update_lines()
        super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        self.update_lines()

    def update_lines(self):
        for line in self.lines:
            line.update_position()

class EdgeLine(QGraphicsLineItem):
    def __init__(self, parent_item, child_item):
        super().__init__()
        self.parent_item = parent_item
        self.child_item = child_item
        self.setPen(QPen(Qt.gray, 2))
        self.setZValue(0)  # 保证线在节点下方
        self.update_position()
        if not hasattr(parent_item, 'lines'):
            parent_item.lines = []
        if not hasattr(child_item, 'lines'):
            child_item.lines = []
        parent_item.lines.append(self)
        child_item.lines.append(self)

    def update_position(self):
        p1 = self.parent_item.scenePos() + self.parent_item.rect().center()
        p2 = self.child_item.scenePos() + self.child_item.rect().center()
        self.setLine(p1.x(), p1.y(), p2.x(), p2.y())