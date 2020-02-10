"""
Generate QR codes for the programming of TOTP devices and apps
"""
from typing import Union, Type

import qrcode
from qrcode.image.base import BaseImage
from qrcode.image.pil import PilImage
from qrcode.image.svg import SvgPathImage, SvgPathFillImage


def create_qr_code_image(
        user: str, data: bytes,
        image_factory: Union[Type[BaseImage], Type[SvgPathImage], Type[SvgPathFillImage], Type[PilImage]] = PilImage,
        block_size: int = 32) -> Union[BaseImage, SvgPathImage, SvgPathFillImage, PilImage]:
    """
    Create a QR code with the Secret

    :param str user: Username to embed in the QR code
    :param bytes data: The secret to embed in the QR code
    :param Union[Type[BaseImage], Type[SvgPathImage], Type[SvgPathFillImage], Type[PilImage]] image_factory:
        The Pillow Image Factory  to use for the QR code generation
    :param int block_size: How large should one block be?
    :rtype: Union[BaseImage, SvgPathImage, SvgPathFillImage, PilImage]
    :returns: The QR Code
    """
    otp_data = 'otpauth://totp/{:s}:{:s}?secret={:s}'.format(
        'Passiopeia-Hub',
        user,
        data.decode('us-ascii')
    )
    qr_code = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_Q,
        box_size=block_size,
        border=4,
    )
    qr_code.add_data(otp_data)
    qr_code.make(fit=True)
    img = qr_code.make_image(image_factory=image_factory)
    return img


def create_transparent_svg_qr_code(user: str, data: bytes, block_size: int = 32) -> SvgPathImage:
    """
    Create a transparent SVG QR code

    :param str user: Username to embed in the QR code
    :param bytes data: The secret to embed in the QR code
    :param int block_size: How large should one block be?
    :rtype: SvgPathImage
    :returns: The QR Code
    """
    return create_qr_code_image(user, data, SvgPathImage, block_size)


def create_svg_qr_code(user: str, data: bytes, block_size: int = 32) -> SvgPathFillImage:
    """
    Create a SVG QR code

    :param str user: Username to embed in the QR code
    :param bytes data: The secret to embed in the QR code
    :param int block_size: How large should one block be?
    :rtype: SvgPathFillImage
    :returns: The QR Code
    """
    return create_qr_code_image(user, data, SvgPathFillImage, block_size)


def create_png_qr_code(user: str, data: bytes, block_size: int = 32) -> PilImage:
    """
    Create a PNG QR code

    :param str user: Username to embed in the QR code
    :param bytes data: The secret to embed in the QR code
    :param int block_size: How large should one block be?
    :rtype: PilImage
    :returns: The QR Code
    """
    return create_qr_code_image(user, data, PilImage, block_size)
