import qrcode
from IPython.display import display

def show_QR_code( data: str, size: int = 10 ) -> None:

    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=size,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    # Create and show image
    img = qr.make_image(fill="black", back_color="white")
    display(img)

    return None

if __name__ == "__main__":
    data = "https://docs.google.com/forms/d/e/1FAIpQLSc3awibbOcxcZEoNJwFef07FhebKcKwwSwVLXPvG9Jl1hI6Wg/viewform?usp=header"  
    show_QR_code( data )
