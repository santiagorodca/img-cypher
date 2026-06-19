# console-line format

from sys import exit
import textwrap


# -----------------------------------------------------------------------------
# CONSTANTES DE CONFIGURACIÓN

__VERSION__ = "1.0"


# -----------------------------------------------------------------------------
# CONSTANTES ANSI

_RESET = "\033[0m"
_BOLD = "\033[1m"
_RED = "\033[31m"
_YELLOW = "\033[33m"


# -----------------------------------------------------------------------------
# FUNCIONES INTERNAS

def _formatear_prompt(mensaje: str) -> str:
    """Asegura que el prompt termine con ': ' para indicar la espera de input."""
    if mensaje.endswith(": "):
        return mensaje
    if mensaje.endswith(":"):
        return mensaje + " "
    return mensaje + ": "


def _envolver(mensaje: str, indent: str) -> str:
    """
    Envuelve el mensaje a un número de caracteres. Las líneas siguientes a la 
    primera se indentan con 'indent' para alinearse con el inicio del texto.
    """
    ancho = 100 - len(indent)
    lineas = textwrap.wrap(mensaje, width = ancho)

    return ("\n" + indent).join(lineas) if lineas else ""


# -----------------------------------------------------------------------------
# TITULO

def mostrar_titulo(titulo: str, version: str = None) -> None:
    """
    Imprime el titulo/encabezado del programa.
 
    :param titulo: Nombre del programa.
    :param version: Versión del programa (opcional).
    """
    if not titulo:
        raise ValueError("El título no puede estar vacío.")
 
    linea = f"// {titulo.upper().strip()}"

    if version is not None:
        linea += f", v{str(version).strip()}"

    print(f"\n{linea}\n")


# -----------------------------------------------------------------------------
# MENSAJES

def mostrar_mensaje(mensaje: str, wrap: bool = True) -> None:
    """
    Imprime un mensaje estándar.

    :param mensaje: Texto a mostrar.
    :param wrap: Ajusta el texto del mensaje dependiendo de su tamaño (opcional).
    """
    indent = "  "   # alinea con el texto después de "> "
    texto = _envolver(mensaje, indent) if wrap else mensaje
    print(f"\n> {texto}")


def mostrar_item(mensaje: str, wrap: bool = True) -> None:
    """
    Imprime un mensaje con formato de lista (sangría + guión).
 
    :param mensaje: Texto a mostrar.
    :param wrap: Ajusta el texto del mensaje dependiendo de su tamaño (opcional).
    """
    indent = "\t  " # alinea con el texto después del "\t- "
    texto = _envolver(mensaje, indent) if wrap else mensaje
    
    print(f"\t- {texto}")


# -----------------------------------------------------------------------------
# ERRORES

def mostrar_error(mensaje: str, item: bool = False, wrap: bool = True) -> None:
    """
    Imprime un mensaje de error en rojo.\n
    Si no es item, agrega un salto de línea automáticamente.
 
    :param mensaje: Texto del error.
    :param item: Usa formato de ítem en lugar del estándar (opcional).
    :param wrap: Ajusta el texto del mensaje dependiendo de su tamaño (opcional).
    """
    sangria = "\t" if item else ""
    sep = "-" if item else ">"
    prefijo = "" if item else "\n"
 
    etiqueta = f"{_RED}{_BOLD}{sep} Error{_RESET}"
    indent = "\t         " if item else "         "
    texto = _envolver(mensaje, indent) if wrap else mensaje

    print(f"{prefijo}{sangria}{etiqueta}: {texto}")
 
    etiquetaItem = f"{_RED}{_BOLD}- Error{_RESET}"
    print(f"\t{etiquetaItem}: No se puede continuar con la ejecución, se detendrá el programa.")
    
    finalizar_programa(False)


# -----------------------------------------------------------------------------
# ADVERTENCIA

def mostrar_advertencia(mensaje: str, item: bool = False, wrap: bool = True) -> None:
    """
    Imprime un mensaje de advertencia en amarillo.\n
    Si no es item, agrega un salto de línea automáticamente.
 
    :param mensaje: Texto de la advertencia.
    :param item: Usa formato de ítem en lugar del estándar (opcional).
    :param wrap: Ajusta el texto del mensaje dependiendo de su tamaño (opcional).
    """
    sangria = "\t" if item else ""
    sep = "-" if item else ">"
    prefijo = "" if item else "\n"
 
    etiqueta = f"{_YELLOW}{_BOLD}{sep} Advertencia{_RESET}"
    indent = "\t               " if item else "               "
    texto = _envolver(mensaje, indent) if wrap else mensaje

    print(f"{prefijo}{sangria}{etiqueta}: {texto}")


# -----------------------------------------------------------------------------
# INPUTS

def pedir_dato(mensaje: str, item: bool = False) -> str:
    """
    Pide un dato al usuario con formato estándar o de ítem.\n
    Siempre devuelve string; vacío si el usuario no ingresó nada.
 
    :param mensaje: Consigna para el usuario.
    :param item: Usa formato de ítem en lugar del estándar (opcional).

    :return: Dato ingresado por el usuario (puede ser vacío).
    """
    sangria = "\t" if item else ""
    sep = "-" if item else ">"
    prefijo = "" if item else "\n"
 
    prompt = f"{prefijo}{sangria}{sep} {_formatear_prompt(mensaje)}"

    return input(prompt).strip()


def pedir_dato_advertencia(mensaje: str, item: bool = False) -> str:
    """
    Pide un dato al usuario con formato de advertencia (amarillo).\n
    Útil cuando se necesita re-ingresar un valor incorrecto.
 
    :param mensaje: Consigna/advertencia para el usuario.
    :param item: Usa formato de ítem en lugar del estándar (opcional).

    :return: Dato ingresado por el usuario (puede ser vacío).
    """
    sangria = "\t" if item else ""
    sep = "-" if item else ">"
    prefijo = "" if item else "\n"
 
    etiqueta = f"{_YELLOW}{_BOLD}{sep} Advertencia{_RESET}"
    prompt = f"{prefijo}{sangria}{etiqueta}: {_formatear_prompt(mensaje)}"

    return input(prompt).strip()


# -----------------------------------------------------------------------------
# FINALIZAR

def finalizar_programa(operacionCompleta: bool = False) -> None:
    """
    Finaliza el programa esperando que el usuario presione Enter.

    :param operacion_completa: Indica si el programa terminó correctamente (opcional).
    """
    if operacionCompleta:
        input("\n// Operación completada, presiona enter para salir...")
    else:
        input("\n// Presiona enter para salir...")
    exit(0)
