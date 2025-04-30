from flask import Blueprint, request
from services.email_service import send_email

bp = Blueprint('email', __name__)

@bp.route("/SendMail")
def send_email_route():

    # curl -X GET "http://localhost:5000/SendMail?recipient_email=test@example.com&subject=Hello&body=This%20is%20a%20test&attachments=/path/to/file1,/path/to/file2"
    params = {
        'recipient_email': request.args.get('recipient_email', ''),
        'subject': request.args.get('subject', 'No Subject'),
        'body': request.args.get('body', 'No Body'),
        'attachments': request.args.get('attachments', '').split(',')
    }
    return send_email(params)
