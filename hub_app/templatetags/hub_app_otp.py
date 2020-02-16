"""
Template Tag for Handling the Login links/dropdowns in templates
"""
from base64 import b64encode, b32encode
from io import BytesIO

from django import template

from hub_app.authlib.totp.qr import create_png_qr_code

register = template.Library()  # pylint: disable=invalid-name


@register.inclusion_tag('hub_app/inclusion/inline-qr-code.html', name='inline_otp_qr_code', takes_context=False)
def do_inline_otp_qr_code(username: str, secret: bytes) -> dict:
    """
    Create an OTP QR Code Inline Image
    """
    with BytesIO() as buffer:
        secret_as_base32 = b32encode(secret)
        create_png_qr_code(username, secret_as_base32, block_size=8).save(buffer)
        buffer_contents = buffer.getvalue()
        buffer_contents_as_base64 = b64encode(buffer_contents)
        buffer_contents_as_string = buffer_contents_as_base64.decode('us-ascii')
        img_src = 'data:image/png;base64,{}'.format(buffer_contents_as_string)
    return {
        'qr_img_data': img_src
    }
