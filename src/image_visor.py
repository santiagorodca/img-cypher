# Copyright 2021 ImagingSolution
# Modified by santiagorodca in 2026.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import tkinter as tk
from PIL import Image, ImageTk
from math import sqrt
from sys import argv
import numpy as np


# --------------------------------------------------------------------------------
# CLASE PRINCIPAL

class Application(tk.Frame):
    ZOOM_MAX = 100.0

    def __init__(self, datosImagen, nombreVentana: str | None = None, master = tk.Tk()):
        super().__init__(master)

        self.master.geometry("1024x576")

        self.imagenPIL = None
        self.titulo = nombreVentana if not nombreVentana == None else "Visor de imágenes"
        self.__old_evento = None        # inicializado para evitar AttributeError
        self._redimensionado = None     # job de debounce para el resize

        self.master.title(self.titulo)

        self.crear_widget()
        self.reiniciar_transformacion()

        # Si se pasa un path, se carga después de que la ventana esté lista
        self.master.after(50, lambda: self.set_imagen(datosImagen))

    # --------------------------------------------------------------------------------
    # Widgets

    def crear_widget(self):
        # Barra de estado
        barraEstado = tk.Frame(self.master, bd = 1, relief = tk.SUNKEN)

        self.texto_infoImagen = tk.Label(barraEstado, text = "información de imagen", anchor = tk.E, padx = 5)
        self.texto_pixelesImagen = tk.Label(barraEstado, text = "(x, y)", anchor = tk.W, padx = 5)

        self.texto_infoImagen.pack(side = tk.RIGHT)
        self.texto_pixelesImagen.pack(side = tk.LEFT)

        barraEstado.pack(side = tk.BOTTOM, fill = tk.X)

        # canvas
        self.canvas = tk.Canvas(self.master, background = "black")
        self.canvas.pack(expand = True, fill = tk.BOTH)

        # eventoos del mouse
        self.master.bind("<Button-1>", self.mouse_clickear)
        self.master.bind("<B1-Motion>", self.mouse_arrastrar)
        self.master.bind("<Motion>", self.mouse_mover)
        self.master.bind("<Double-Button-1>", self.mouse_doble_click)
        self.master.bind("<MouseWheel>", self.mouse_rueda)

        # resize responsivo: re-fit cuando cambia el tamaño del canvas
        self.canvas.bind("<Configure>", self.ajustar_canvas)


    def set_imagen(self, archivo):
        if not archivo:
            return
        
        self.imagenPIL = Image.open(archivo)

        self.arreglar_zoom(self.imagenPIL.width, self.imagenPIL.height)
        self.dibujar_imagen(self.imagenPIL)

        self.texto_infoImagen["text"] = (
            f"{self.imagenPIL.format} : "
            f"{self.imagenPIL.width} x {self.imagenPIL.height} "
            f"{self.imagenPIL.mode}"
        )

    # --------------------------------------------------------------------------------
    # eventos del mouse

    def mouse_clickear(self, evento):
        self.__old_evento = evento


    def mouse_arrastrar(self, evento):
        if self.imagenPIL is None or self.__old_evento is None:
            return
        
        self.transformar(evento.x - self.__old_evento.x, evento.y - self.__old_evento.y)
        self.clamp_pan()

        self.redibujar_imagen()
        self.__old_evento = evento


    def mouse_mover(self, evento):
        if self.imagenPIL is None:
            return
        
        image_point = self.punto_imagen(evento.x, evento.y)

        # usamos len() en vez de "!= []" para evitar ValueError con arrays numpy
        if len(image_point) > 0:
            self.texto_pixelesImagen["text"] = f"({image_point[0]:.0f}, {image_point[1]:.0f})"
        else:
            self.texto_pixelesImagen["text"] = "(--, --)"


    def mouse_doble_click(self, evento):
        if self.imagenPIL is None:
            return
        
        self.arreglar_zoom(self.imagenPIL.width, self.imagenPIL.height)
        self.redibujar_imagen()


    def mouse_rueda(self, evento):
        if self.imagenPIL is None:
            return
        
        if evento.delta < 0:
            self.escalar_a(0.8, evento.x, evento.y)     # acercar
        else:
            self.escalar_a(1.25,  evento.x, evento.y)   # alejar

        self.redibujar_imagen()


    def ajustar_canvas(self, evento):
        if self.imagenPIL is None:
            return
        
        # cancelar el job anterior para no redibujar en cada píxel del resize
        if self._redimensionado is not None:
            self.master.after_cancel(self._redimensionado)

        self._redimensionado = self.master.after(80, self._aplicar_redimension)


    def _aplicar_redimension(self):
        """Aplica arreglar_zoom al nuevo tamaño del canvas."""
        self._redimensionado = None

        if self.imagenPIL is None:
            return
        
        self.arreglar_zoom(self.imagenPIL.width, self.imagenPIL.height)
        self.redibujar_imagen()


    # -------------------------------------------------------------------------------
    # TRANSFORMACIONES

    def reiniciar_transformacion(self):
        self.mat_affine = np.eye(3)


    def obtener_escala_actual(self):
        """Escala actual extraída de la matriz afín."""
        return sqrt(self.mat_affine[0, 0] ** 2 + self.mat_affine[1, 0] ** 2)


    def obtener_escala_ajustada(self):
        """Escala mínima: la que usa arreglar_zoom para ajustar la imagen al canvas actual."""
        if self.imagenPIL is None:
            return 1.0
        
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()

        iw = self.imagenPIL.width
        ih = self.imagenPIL.height

        return (ch / ih) if (cw * ih > iw * ch) else (cw / iw)


    def transformar(self, desplazamientoX, desplazamientoY):
        mat = np.eye(3)
        mat[0, 2] = float(desplazamientoX)
        mat[1, 2] = float(desplazamientoY)

        self.mat_affine = np.dot(mat, self.mat_affine)


    def escalar(self, escalar: float):
        mat = np.eye(3)
        mat[0, 0] = escalar
        mat[1, 1] = escalar

        self.mat_affine = np.dot(mat, self.mat_affine)


    def escalar_a(self, escalar: float, cx: float, cy: float):
        """
        Escala centrado en (cx, cy).
        - Límite mínimo: no se puede alejar más del arreglar_zoom (imagen cabe justo en pantalla).
        - Límite máximo: no se puede acercar más de ZOOM_MAX px-pantalla por px-imagen.
        """
        actual = self.obtener_escala_actual()
        nuevaEscala = actual * escalar

        if escalar < 1.0 and nuevaEscala < self.obtener_escala_ajustada():
            return      # límite mínimo

        if escalar > 1.0 and nuevaEscala > self.ZOOM_MAX:
            return      # límite máximo

        self.transformar(-cx, -cy)
        self.escalar(escalar)
        self.transformar(cx, cy)
        self.clamp_pan()


    def clamp_pan(self):
        """
        Límite estricto de desplazamiento:
        - Si la imagen es más grande que el canvas (zoom in): los bordes de la
          imagen no pueden retroceder más allá del borde del canvas — nunca
          se ve el fondo negro detrás de la imagen.
        - Si la imagen es más chica que el canvas (zoom out): la imagen queda
          centrada y no se puede mover.
        """
        if self.imagenPIL is None:
            return

        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        iw = self.imagenPIL.width
        ih = self.imagenPIL.height

        # Proyectar las 4 esquinas de la imagen al espacio del canvas
        esquinas = [(0, 0, 1), (iw, 0, 1), (iw, ih, 1), (0, ih, 1)]
        puntos = [np.dot(self.mat_affine, c) for c in esquinas]

        min_x = min(p[0] for p in puntos)
        max_x = max(p[0] for p in puntos)
        min_y = min(p[1] for p in puntos)
        max_y = max(p[1] for p in puntos)

        img_w = max_x - min_x   # ancho de la imagen en píxeles de pantalla
        img_h = max_y - min_y   # alto  de la imagen en píxeles de pantalla

        dx, dy = 0.0, 0.0

        if img_w >= cw:
            # Imagen más ancha que el canvas: los bordes no pueden
            # alejarse del borde del canvas (no se ve fondo negro)
            if min_x > 0:
                dx = -min_x          # borde izquierdo se fue a la derecha
            elif max_x < cw:
                dx = cw - max_x      # borde derecho se fue a la izquierda
        else:
            # Imagen más angosta: centrar horizontalmente, sin movimiento
            dx = (cw - img_w) / 2 - min_x

        if img_h >= ch:
            # Imagen más alta que el canvas: ídem para el eje Y
            if min_y > 0:
                dy = -min_y          # borde superior se fue hacia abajo
            elif max_y < ch:
                dy = ch - max_y      # borde inferior se fue hacia arriba
        else:
            # Imagen más baja: centrar verticalmente, sin movimiento
            dy = (ch - img_h) / 2 - min_y

        if dx != 0.0 or dy != 0.0:
            self.transformar(dx, dy)


    def arreglar_zoom(self, anchoImagen, alturaImagen):
        """Ajusta la imagen para que quepa exactamente en el canvas actual."""
        anchuraCanvas = self.canvas.winfo_width()
        alturaCanvas = self.canvas.winfo_height()

        if (anchoImagen * alturaImagen <= 0) or (anchuraCanvas * alturaCanvas <= 0):
            return

        self.reiniciar_transformacion()

        if (anchuraCanvas * alturaImagen) > (anchoImagen * alturaCanvas):
            escala = alturaCanvas / alturaImagen
            desplazamientoX = (anchuraCanvas - anchoImagen * escala) / 2
            desplazamientoY = 0.0
        else:
            escala = anchuraCanvas / anchoImagen
            desplazamientoX = 0.0
            desplazamientoY = (alturaCanvas - alturaImagen * escala) / 2

        self.escalar(escala)
        self.transformar(desplazamientoX, desplazamientoY)


    def punto_imagen(self, x, y):
        if self.imagenPIL is None:
            return []
        
        mat_inv = np.linalg.inv(self.mat_affine)
        image_point = np.dot(mat_inv, (x, y, 1.0))

        if (image_point[0] < 0 or image_point[1] < 0
                or image_point[0] > self.imagenPIL.width
                or image_point[1] > self.imagenPIL.height):
            return []
        
        return image_point

    # -------------------------------------------------------------------------------
    # DIBUJO

    def dibujar_imagen(self, imagenPIL):
        if imagenPIL is None:
            return

        self.imagenPIL = imagenPIL

        anchuraCanvas  = self.canvas.winfo_width()
        alturaCanvas = self.canvas.winfo_height()

        mat_inv = np.linalg.inv(self.mat_affine)

        affine_inv = (
            mat_inv[0, 0], mat_inv[0, 1], mat_inv[0, 2],
            mat_inv[1, 0], mat_inv[1, 1], mat_inv[1, 2],
        )

        dst = self.imagenPIL.transform(
            (anchuraCanvas, alturaCanvas),
            Image.AFFINE,
            affine_inv,
            Image.NEAREST,
        )

        im = ImageTk.PhotoImage(image = dst)
        self.canvas.create_image(0, 0, anchor = "nw", image = im)
        self.image = im     # evitar que el GC elimine la referencia


    def redibujar_imagen(self):
        if self.imagenPIL is None:
            return
        
        self.dibujar_imagen(self.imagenPIL)


if __name__ == "__main__":
    if len(argv) > 1:
        app = Application(argv[1]).mainloop()