# img-cypher

Un pequeño cifrador de archivos de imágenes mediante una contraseña.


## ¿Cómo funciona?

Es un programa hecho para interfaces CLI (Command Line Interface) donde cifrará tu archivo `.png`, `.jpg`, `.webp`, entre otros formatos de imagen soportados por la librería PIL, mediante una contraseña para encriptar/desencriptar el archivo. Ten en cuenta que si pierdes la clave, **no podrás recuperar esa imagen**.

Existen formatos de imagen que traen compresión y otros que no. Este programa identifica dichos formatos y les aplica una compresión hecha por **zstandard**.

El archivo de salida tiene como formato `.enxi`, donde contiene los datos cifrados de la imagen.

El programa cuenta con un visualizador de imágenes para mostrar los archivos desencriptados. De esta forma, la imagen desencriptada no se guarda en el disco como archivo temporal, sino que permanece en la memoria RAM úncamente para su visualización.

> El script para visualizar imágenes (`image_visor.py`) es una versión modificada del script original de [ImagingSolution](https://github.com/ImagingSolution), obtenido de [PythonImageViewer](https://github.com/ImagingSolution/PythonImageViewer). Este código se utiliza bajo los términos de la Licencia Apache 2.0.


## Ejecución

```
python image_cypher.py "ruta/imagen"
```

> El programa deduce automáticamente la extención del archivo con su firma interna.


### Parámetros

| Parámetro | Explicación |
| --------- | ----------- |
| `--export` | Solo con archivos `.enxi`. Al desencriptar, guarda los datos en un archivo en el disco con el mismo formato que soporta la imagen. |
| `--delete` | Elimina el archivo de entrada (input). Funciona solo cuando se encripta, y se desencripta la imagen y se quiere exportar. |
| `--help` | Muestra un menú de ayuda básica. |


### Ejemplo con parámetros

```
python image_cypher.py --export "imagen.enxi"
```


## Compilación

Podés ejecutar este programa como vos quieras, pero si querés compilarlo, te recomiendo que lo hagas por `pyinstaller`. Ten en cuenta que creará un ejecutable para el sistema operativo que estés usando (Windows/Linux/MacOS).


### Pasos

1. Si no lo tenés instalado, podés hacerlo con: `pip install pyinstaller`.

2. En la carpeta del repositorio, ejecutás el comando `pyinstaller --onefile ./src/image_cypher.py` (versión de Windows). Empezará a analizar el código del programa para compilarlo.

3. Luego de un breve tiempo, tendrás una nueva carpeta `dist/` donde estará el ejecutable para usarlo.


## Librerías usadas

- `cryptography`
- `numpy`
- `PIL`
- `tkinter`
- `zstandard`
- `cl_format` (módulo de formato por consola propio)

> En requirements.txt están las versiones compatibles (por lo menos las que yo probé).


## Licencia

Este proyecto está regido bajo la licencia Apache 2.0


## Contribución

Si querés contribuir al proyecto, no tengo problema en revisar tu pull request y aprobarlo. Cada pull tendrá que explicar el código o los cambios que solicita.