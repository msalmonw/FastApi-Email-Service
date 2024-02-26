from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
import aiosmtplib
from email.message import EmailMessage
#from python_socks.async_ import ProxyType, create_proxy_connector
import socks

app = FastAPI()

# Pydantic models for the input data
class SMTPDetails(BaseModel):
    username: str
    password: str
    server: str # Format: hostname:port
    use_tls: bool = True  # Enable TLS by default

class ProxyDetails(BaseModel):
    host: str
    port: int
    username: str = None  # Optional: for proxy authentication
    password: str = None  # Optional: for proxy authentication

class EmailPayload(BaseModel):
    sender_email: EmailStr
    sender_name: str
    recipient_email: EmailStr
    subject: str
    html_content: str
    text_content: str

@app.post("/send-email/")
async def send_email(smtp_details: SMTPDetails, proxy_details: ProxyDetails, email_payload: EmailPayload):
    # Parse SMTP server and port
    smtp_server, smtp_port = smtp_details.server.split(":")
    smtp_port = int(smtp_port)  # Convert port to integer

    # Create a proxy connector with or without authentication

    if proxy_details.username and proxy_details.password:
        '''connector = await create_proxy_connector(
            proxy_type=ProxyType.SOCKS5,
            host=proxy_details.host,
            port=proxy_details.port,
            username=proxy_details.username,
            password=proxy_details.password
        )'''
        socks.set_default_proxy(
            proxy_type=socks.SOCKS5, 
            addr=proxy_details.host, 
            port=proxy_details.port,
            username=proxy_details.username,
            password=proxy_details.password
            )
    else:
        '''connector = await create_proxy_connector(
            proxy_type=ProxyType.SOCKS5,
            host=proxy_details.host,
            port=proxy_details.port
        )'''
        socks.set_default_proxy(
            proxy_type=socks.SOCKS5, 
            addr=proxy_details.host, 
            port=proxy_details.port
            )
    
    try:
   
        # SMTP client configuration
        smtp_client = aiosmtplib.SMTP(hostname=smtp_server, port=smtp_port, use_tls=smtp_details.use_tls, sock=socks.socksocket())

        # Connect to the SMTP server using the proxy
        await smtp_client.connect()
        
        # Login to the SMTP server
        await smtp_client.login(smtp_details.username, smtp_details.password)

        # Construct the email message
        message = EmailMessage()
        message["From"] = f"{email_payload.sender_name} <{email_payload.sender_email}>"
        message["To"] = email_payload.recipient_email
        message["Subject"] = email_payload.subject
        message.set_content(email_payload.text_content)  # Set text content
        message.add_alternative(email_payload.html_content, subtype="html")  # Set HTML content

        # Send the email
        await smtp_client.send_message(message)

        # Properly close the SMTP connection
        await smtp_client.quit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"message": "Email sent successfully!"}


if __name__=='__main__':
    import uvicorn
    uvicorn.run(app=app)
