from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from io import BytesIO
from os import urandom
from pathlib import Path
from PIL import Image
from zstandard import ZstdCompressor, ZstdDecompressor
import cl_format as cl
from time import time
from sys import argv, exit
from os import remove


# --------------------------------------------------------------------------------
# CONSTANTES

_VERSION = 1

FORMATO_SALIDA = ".enxi"
_FIRMA = b"ENXI" # 4b

# constantes de configuración para futuras updates
TAMANO_BYTES_LECTURA = 1_048_576    # 1mb
ITERACIONES = 600_000


# --------------------------------------------------------------------------------
# FUNCIONES

def generar_encabezado(salt: bytes, nonce: bytes, enxiComprimido: bool) -> bytes:
    # Patrón: enxi|version|salt|nonce|fecha|comprimido
    encabezado: bytes = _FIRMA
    encabezado += _VERSION.to_bytes(1, "little")        # 5b (4b [firma] + 1b)

    encabezado += salt                                  # 16b
    encabezado += nonce                                 # 12b
    encabezado += int(time()).to_bytes(4, "little")     # 4b
    encabezado += b"1" if enxiComprimido else b"0"      # 1b

    return encabezado                                   # 38b


def derivar_clave(contrasena: str, salt: bytes) -> bytes:
    return PBKDF2HMAC(hashes.SHA256(), 32, salt, ITERACIONES).derive(contrasena.encode())


def eliminar_archivo():
    if DELETE:
        remove(RUTA_ENTRADA)


def encriptar_imagen(contrasena: str, originalComprimido: bool) -> None:
    archivoSalida = RUTA_ENTRADA.parent.joinpath(RUTA_ENTRADA.stem + FORMATO_SALIDA)
    
    with RUTA_ENTRADA.open("rb") as imagenEntrada, archivoSalida.open("wb") as imagenSalida:
        if not originalComprimido:
            datosCrudos = ZstdCompressor(level = 22, write_content_size = True).compress(imagenEntrada.read())
        else:
            datosCrudos = imagenEntrada.read()
        
        imagenEntrada.close()

        SALT = urandom(16)
        NONCE = urandom(12)
        
        encabezado = generar_encabezado(SALT, NONCE, not originalComprimido)

        clave = derivar_clave(contrasena, SALT)

        imagenSalida.write(encabezado)
        imagenSalida.write(AESGCM(clave).encrypt(NONCE, datosCrudos, encabezado))

        imagenSalida.close()
    
    cl.mostrar_mensaje(f"Imagen encriptada en: {archivoSalida}", False)

    eliminar_archivo()    
    cl.finalizar_programa(True)


def desencriptar_imagen(contrasena: str):
    with RUTA_ENTRADA.open("rb") as imagenEntrada:
        # Patrón: enxi|version|salt|nonce|fecha|comprimido
        firma = imagenEntrada.read(4)
        version = imagenEntrada.read(1)
        salt = imagenEntrada.read(16)
        nonce = imagenEntrada.read(12)
        fecha = imagenEntrada.read(4)
        enxiComprimido = imagenEntrada.read(1)

        encabezado = firma + version + salt + nonce + fecha + enxiComprimido

        # lo verificamos de nuevo, por las dudas
        if firma != b"ENXI":
            cl.mostrar_error("El formato interno del archivo no es válido.")

        clave = derivar_clave(contrasena, salt)

        try:
            datosDesencriptados = AESGCM(clave).decrypt(nonce, imagenEntrada.read(), encabezado)
        except Exception:
            cl.mostrar_error("No se pudo desencriptar la imagen. Es posible que la contraseña sea incorrecta o que los datos hallan sido alterados.")
        imagenEntrada.close()

    # resuelve la compresión del archivo
    if enxiComprimido == b"1":
        datosDesencriptados = ZstdDecompressor().decompress(datosDesencriptados)

    # si de marcó el parámetro para exportar la imágen, pasa esto:
    if EXPORT:
        cl.mostrar_mensaje("Exportando imagen...")
        
        with Image.open(BytesIO(datosDesencriptados)) as img:
            try:
                formato = img.format
            except Image.UnidentifiedImageError as eUIE:
                cl.mostrar_error(f"Hubo un error al abrir la imagen guardada y obtener sus datos: {eUIE}")
            img.close()

        rutaSalida = RUTA_ENTRADA.parent.joinpath(RUTA_ENTRADA.stem + "." + formato.lower())

        with open(rutaSalida, "wb") as imagenSalida:
            imagenSalida.write(datosDesencriptados)
            imagenSalida.close()

        cl.mostrar_mensaje(f"Imagen exportada en: {rutaSalida}", False)

        eliminar_archivo()
        cl.finalizar_programa(True)

    cl.mostrar_mensaje("Cargando imagen...")
    try:
        import image_visor

        image_visor.Application(BytesIO(datosDesencriptados), "Visor de imágenes cifradas").mainloop()
    except Exception as eE:
        cl.mostrar_error("Hubo un error al cargar la imagen: " + eE)

    # se sale del programa =)
    exit(0)


def extraer_datos_basicos_imagen(sufijoArchivo: str) -> tuple[bool, bool | None]:     # bools: esFormatoEnxi, estaComprimido
    # PIL v12.1.1
    # Abre la imagen y extrae información como la firma y la info
    if sufijoArchivo in ".enxi":
        with open(RUTA_ENTRADA, "rb") as enxiImg:
            formatoImagen = enxiImg.read(4)
            enxiImg.close()

    if sufijoArchivo in Image.registered_extensions() or sufijoArchivo == ".txt":
        with Image.open(RUTA_ENTRADA) as img:
            try:
                info = img.info
                formatoImagen = img.format
            except Exception as eE:
                cl.mostrar_error(f"Hubo un error al abrir la imagen y obtener sus datos: {eE}")
            img.close()
    
    # con los datos obtenidos, verificamos si la imagen tiene nuestra firma
    # si es así, retorna los datos obtenidos
    if formatoImagen == _FIRMA:
        return True, None

    # si no tiene nuestra firma, pasamos a verificar todos los formatos
    # compatibles con PIL. en este caso, verificamos que el archivo SEA una
    # imagen real. para eso, descartamos los formatos que no lo cumplen.
    if formatoImagen in ["MPEG", "PDF", "BUFR", "GRIB", "HDF5", "WMF", "IPTC", "FTEX"]:
        cl.mostrar_error("El formato del archivo no es compatible con el programa.")

    # luego, verificamos si el archivo YA está comprimido. para esto, revisamos
    # si la extención forma parte de una lista de formatos comprimidos
    if formatoImagen in ["AVIF", "BLP", "CUR", 'PCX', 'DCX', 'DDS', 'EPS', "FLI", "GBR", "GIF", "PNG", "JPEG2000", "ICNS", "ICO", "JPEG", "MPO", "MSP", "PALM", "PCD", "PIXAR", "PSD", "QOI", "WEBP"]:
        return False, True

    # como último caso, revisamos cada formato donde puede ser comprimido
    estaComprimido = False

    if formatoImagen in ("TIFF"):
        comp = getattr(img, "tag_v2", {}).get(259, 1)
        estaComprimido = comp != 1  # 1 = sin compresión

    if formatoImagen in ("BMP", "DIB"):
        estaComprimido = info.get("compression", 0) != 0

    if formatoImagen in ("SGI"):
        estaComprimido = bool(info.get("rle", False))

    # TGA y RAS requieren leer el header binario
    if formatoImagen in ("TGA"):
        with open(RUTA_ENTRADA, "rb") as f:
            f.seek(2)
            estaComprimido = f.read(1)[0] in (9, 10, 11)

    if formatoImagen == "SUN":
        with open(RUTA_ENTRADA, "rb") as f:
            f.seek(20)
            estaComprimido = int.from_bytes(f.read(4), "big") == 2

    return False, estaComprimido


def main(contrasena: str) -> None:
    cl.mostrar_mensaje("Analizando...")

    # Obtiene el formato de la imagen o del archivo
    sufijoArchivo = RUTA_ENTRADA.suffix.lower()

    if not sufijoArchivo in Image.registered_extensions() and not sufijoArchivo in [".txt", ".enxi"]:   # El .txt es para propósito personal
        cl.mostrar_error("El formato de la imagen no es compatible para su procesamiento.")

    esFormatoEnxi, estaComprimido = extraer_datos_basicos_imagen(sufijoArchivo)

    # Analizando contraseña
    if len(contrasena) < 8 and not esFormatoEnxi:
        cl.mostrar_advertencia("La contraseña es demasiado corta. Es recomenbable establecer una longitud mínima de 8 caracteres para garantizar la seguridad de la imagen.")

    # Desencripta
    if esFormatoEnxi:
        cl.mostrar_mensaje("Desencriptando imagen...")
        desencriptar_imagen(contrasena)
    else:
        # De última, encripta el archivo
        cl.mostrar_mensaje("Encriptando imagen...")
        encriptar_imagen(contrasena, estaComprimido)
    

# Entry Point
if __name__ == "__main__":
    cl.mostrar_titulo("cifrador de imágenes", str(_VERSION))

    if "--help" in argv:
        cl.mostrar_mensaje("Programa que brinda una capa de protección y privacidad a sus imágenes.")
        cl.mostrar_mensaje("Parámetros")
        cl.mostrar_item("\"--export\": Convierte la imagen ENXI a su formato original.")
        cl.mostrar_item("\"--delete\": Elimina el archivo de entrada luego de convertirlo de un formato a otro. Funciona solo cuando se encripta, y cuando se desencripta la imagen y se quiere exportar.")
        cl.mostrar_item("\"--help\": Muestra este mismo menú de ayuda.\n")
        exit(0)

    # Extrae los parámetros
    global EXPORT, DELETE, RUTA_ENTRADA
    EXPORT = "--export" in argv
    DELETE = "--delete" in argv

    # Verifica la existencia del archivo añadido como parámetro para continuar.
    if len(argv) > 1:
        RUTA_ENTRADA = Path(argv.pop())

        if not RUTA_ENTRADA.exists():
            cl.mostrar_error("El archivo no fue importado o no existe.")

        contrasena = cl.pedir_dato("Inserte la contraseña")

        main(contrasena)

    RUTA_ENTRADA = Path(cl.pedir_dato("Inserte la ruta del archivo").replace("\"", ""))
    contrasena = cl.pedir_dato("Inserte la contraseña")

    main(contrasena)