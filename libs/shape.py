#!/usr/bin/python
# -*- coding: utf-8 -*-


try:
    from PyQt5.QtGui import *
    from PyQt5.QtCore import *
except ImportError:
    from PyQt4.QtGui import *
    from PyQt4.QtCore import *

from libs.utils import distance
import math
import sys

DEFAULT_LINE_COLOR = QColor(0, 255, 0, 128)
DEFAULT_FILL_COLOR = QColor(255, 0, 0, 128)
DEFAULT_SELECT_LINE_COLOR = QColor(255, 255, 255)
DEFAULT_SELECT_FILL_COLOR = QColor(0, 128, 255, 155)
DEFAULT_VERTEX_FILL_COLOR = QColor(0, 255, 0, 255)
DEFAULT_HVERTEX_FILL_COLOR = QColor(255, 0, 0)


class Shape(object):
    P_SQUARE, P_ROUND = range(2)

    MOVE_VERTEX, NEAR_VERTEX = range(2)

    # The following class variables influence the drawing
    # of _all_ shape objects.
    line_color = DEFAULT_LINE_COLOR
    fill_color = DEFAULT_FILL_COLOR
    select_line_color = DEFAULT_SELECT_LINE_COLOR
    select_fill_color = DEFAULT_SELECT_FILL_COLOR
    vertex_fill_color = DEFAULT_VERTEX_FILL_COLOR
    h_vertex_fill_color = DEFAULT_HVERTEX_FILL_COLOR
    point_type = P_ROUND
    point_size = 16
    scale = 1.0
    label_font_size = 8

    def __init__(self, label=None, line_color=None, difficult=False, paint_label=False, is_rotated=False):
        self.label = label
        self.points = []
        self.fill = False
        self.selected = False
        self.difficult = difficult
        self.paint_label = paint_label

        self.direction = 0
        self.center = None
        self.is_rotated = is_rotated
        print("SHAPE")

        self._highlight_index = None
        self._highlight_mode = self.NEAR_VERTEX
        self._highlight_settings = {
            self.NEAR_VERTEX: (4, self.P_ROUND),
            self.MOVE_VERTEX: (1.5, self.P_SQUARE),
        }

        self._closed = False

        if line_color is not None:
            # Override the class line_color attribute
            # with an object attribute. Currently this
            # is used for drawing the pending line a different color.
            self.line_color = line_color

    def getCourtSizes(self, width, height):
        half_court_height = height * 0.5
        service_box_height = height * 0.27
        no_mans_land_height = height * 0.23
        alley_width = width * 0.12
        service_box_width = width * 0.38

        return [half_court_height, service_box_height, no_mans_land_height, alley_width, service_box_width]

    def rotate(self, theta):
        for i, p in enumerate(self.points):
            self.points[i] = self.rotate_point(p, theta)
        self.direction -= theta
        self.direction = self.direction % (2 * math.pi)
    
    def rotate_point(self, p, theta):
        order = p - self.center
        cosTheta = math.cos(theta)
        sinTheta = math.sin(theta)
        pResx = cosTheta * order.x() + sinTheta * order.y()
        pResy = - sinTheta * order.x() + cosTheta * order.y()
        pRes = QPointF(self.center.x() + pResx, self.center.y() + pResy)
        return pRes

    def close(self):
        self.center = QPointF((self.points[0].x()+self.points[2].x()) / 2, (self.points[0].y()+self.points[2].y()) / 2)
        self._closed = True

    def reach_max_points(self):
        if len(self.points) >= 4:
            return True
        return False

    def add_point(self, point):
        if not self.reach_max_points():
            self.points.append(point)

    def pop_point(self):
        if self.points:
            return self.points.pop()
        return None

    def is_closed(self):
        return self._closed

    def set_open(self):
        self._closed = False

    def paint(self, painter):
        if self.points:
            color = self.select_line_color if self.selected else self.line_color
            pen = QPen(color)
            # Try using integer sizes for smoother drawing(?)
            pen.setWidth(max(1, int(round(2.0 / self.scale))))
            painter.setPen(pen)

            line_path = QPainterPath()
            vertex_path = QPainterPath()

            line_path.moveTo(self.points[0])
            # Uncommenting the following line will draw 2 paths
            # for the 1st vertex, and make it non-filled, which
            # may be desirable.
            # self.drawVertex(vertex_path, 0)

            for i, p in enumerate(self.points):
                line_path.lineTo(p)
                self.draw_vertex(vertex_path, i)
            if self.is_closed():
                line_path.lineTo(self.points[0])

            painter.drawPath(line_path)
            painter.drawPath(vertex_path)
            painter.fillPath(vertex_path, self.vertex_fill_color)

            # Draw text at the top-left
            min_x = sys.maxsize
            min_y = sys.maxsize
            max_x = -1
            max_y = -1
            min_y_label = int(1.25 * self.label_font_size)
            for point in self.points:
                min_x = min(min_x, point.x())
                min_y = min(min_y, point.y())
                max_x = max(max_x, point.x())
                max_y = max(max_y, point.y())
            if self.paint_label:
                if min_x != sys.maxsize and min_y != sys.maxsize:
                    font = QFont()
                    font.setPointSize(self.label_font_size)
                    font.setBold(True)
                    painter.setFont(font)
                    if self.label is None:
                        self.label = ""
                    if min_y < min_y_label:
                        min_y += min_y_label
                    painter.drawText(int(min_x), int(min_y), self.label)

            if self.fill:
                color = self.select_fill_color if self.selected else self.fill_color
                painter.fillPath(line_path, color)
            
            if self.center is not None and self.is_rotated:
                center_path = QPainterPath()
                d = self.point_size / self.scale
                center_path.addRect(self.center.x() - d / 2, self.center.y() - d / 2, d, d)
                painter.drawPath(center_path)
                painter.fillPath(center_path, self.vertex_fill_color)
                # Draw tennis court # TODO calculate this better when rotated
                rect_width = max_x - min_x
                rect_height = max_y - min_y

                half_court_height, service_box_height, no_mans_land_height, alley_width, service_box_width = self.getCourtSizes(rect_width, rect_height)
                # Outer court
                painter.drawRect(int(min_x), int(min_y), int(rect_width), int(rect_height))
                # Court alleys
                painter.drawRect(int(min_x), int(min_y), int(alley_width), int(rect_height))
                painter.drawRect(int(min_x + rect_width - alley_width), int(min_y), int(alley_width), int(rect_height))
                # Service boxes
                painter.drawRect(int(min_x + alley_width), int(min_y + no_mans_land_height), int(service_box_width), int(service_box_height))
                painter.drawRect(int(min_x + alley_width + service_box_width), int(min_y + no_mans_land_height), int(service_box_width), int(service_box_height))
                painter.drawRect(int(min_x + alley_width), int(min_y + no_mans_land_height + service_box_height), int(service_box_width), int(service_box_height))
                painter.drawRect(int(min_x + alley_width + service_box_width), int(min_y + no_mans_land_height + service_box_height), int(service_box_width), int(service_box_height))

    def draw_vertex(self, path, i):
        d = self.point_size / self.scale
        shape = self.point_type
        point = self.points[i]
        if i == self._highlight_index:
            size, shape = self._highlight_settings[self._highlight_mode]
            d *= size
        if self._highlight_index is not None:
            self.vertex_fill_color = self.h_vertex_fill_color
        else:
            self.vertex_fill_color = Shape.vertex_fill_color
        if shape == self.P_SQUARE:
            path.addRect(point.x() - d / 2, point.y() - d / 2, d, d)
        elif shape == self.P_ROUND:
            path.addEllipse(point, d / 2.0, d / 2.0)
        else:
            assert False, "unsupported vertex shape"

    def nearest_vertex(self, point, epsilon):
        index = None
        for i, p in enumerate(self.points):
            dist = distance(p - point)
            if dist <= epsilon:
                index = i
                epsilon = dist
        return index

    def contains_point(self, point):
        return self.make_path().contains(point)

    def make_path(self):
        path = QPainterPath(self.points[0])
        for p in self.points[1:]:
            path.lineTo(p)
        return path

    def bounding_rect(self):
        return self.make_path().boundingRect()

    def move_by(self, offset):
        self.points = [p + offset for p in self.points]

    def move_vertex_by(self, i, offset):
        self.points[i] = self.points[i] + offset

    def highlight_vertex(self, i, action):
        self._highlight_index = i
        self._highlight_mode = action

    def highlight_clear(self):
        self._highlight_index = None

    def copy(self):
        shape = Shape("%s" % self.label)
        shape.points = [p for p in self.points]

        shape.center = self.center
        shape.direction = self.direction
        shape.is_rotated = self.is_rotated

        shape.fill = self.fill
        shape.selected = self.selected
        shape._closed = self._closed
        if self.line_color != Shape.line_color:
            shape.line_color = self.line_color
        if self.fill_color != Shape.fill_color:
            shape.fill_color = self.fill_color
        shape.difficult = self.difficult
        return shape

    def __len__(self):
        return len(self.points)

    def __getitem__(self, key):
        return self.points[key]

    def __setitem__(self, key, value):
        self.points[key] = value
