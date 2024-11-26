import re
from datetime import datetime
import imaplib
from email import message_from_bytes
from email.parser import BytesParser
from email.mime.message import MIMEMessage
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from email.header import decode_header
from dateutil import parser
from transformers import pipeline
from models import Public_Events
import pytz
from config import db, app
import ssl

mail = None
qa_pipeline = pipeline("question-answering", model="distilbert-base-uncased-distilled-squad")
summarizer = pipeline("summarization", model="t5-small")
classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

def get_unique_num(events):
    max = 0
    for event in events:
        try:
            id = int(event.event_id)
        except:
            continue
        if id > max:
            max = id
    return max+1

def get_status_and_msg():
    IMAP_SERVER = 'imap.iitb.ac.in'
    IMAP_USER = #INSERT YOUR LDAP USER ID HERE
    IMAP_PASSWORD = #INSERT YOUR MAIL ACCESS TOKEN HERE
    CIPHER = #INSERT YOUR CIPHER HERE
    last_read = '25-Nov-2024'
    
    IMAP_PORT = 993
    SENDER_TO = 'student-notices@iitb.ac.in'
    imap_ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    imap_ssl_context.options |= ssl.OP_NO_SSLv2 | ssl.OP_NO_SSLv3
    imap_ssl_context.set_ciphers(CIPHER)

    global mail
    mail = imaplib.IMAP4_SSL(IMAP_SERVER, port=IMAP_PORT, ssl_context=imap_ssl_context)
    mail.login(IMAP_USER, IMAP_PASSWORD)
    mail.select("INBOX")

    if last_read:
        search_criteria = f'(SINCE "{last_read}" TO "{SENDER_TO}" SUBJECT "[Student-notices]")'
    else:
        search_criteria = f'(TO "{SENDER_TO}" SUBJECT "[Student-notices]")'
    
    status, message_ids = mail.search(None, search_criteria)
    if status != "OK":
        return None
    print(message_ids)
    with open('/home/srikar/Documents/sl_project', 'r+') as file:
        lines = file.readlines()
        lines[4] = datetime.now().strftime('%d-%b-%Y') + '\n'
        file.seek(0)
        file.writelines(lines)
        file.truncate()

    return message_ids

def get_emails(messages):
    email_ids = messages[0].split()
    data = []
    global mail
    for ids in email_ids:
        status,msg = mail.fetch(ids,"(RFC822)")
        if status != 'OK':
            print(f"Failed to fetch email")
            continue
        data.append(msg)
    return data

def get_subject(msg):
    decoded_subject = ""
    for part, encoding in decode_header(msg['Subject']):
        if isinstance(part, bytes):
            part = part.decode(encoding or 'utf-8')
        decoded_subject += part
    subject = re.sub(r"^(Re:\s*)?\[Student-notices\]\s*", "", decoded_subject)
    if "Fwd" in subject:
        subject = re.sub(r"(?i)^.*Fwd:\s*", "", subject)
    if "Adult vaccination" in subject:
        return "NO"
    return subject

def get_body(msg):
    plain_count = 0
    body = None
    if msg.is_multipart():
        print("Multipart message detected")
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = part.get("Content-Disposition", "")

            if content_type == "text/plain" and "attachment" not in content_disposition:
                try:
                    text = part.get_payload(decode=True).decode(part.get_content_charset() or "utf-8")
                except Exception as e:
                    print(f"Error decoding payload: {e}")
                    continue
                plain_count += 1
                if plain_count == 2:
                    marker = "-------- Original Message --------"
                    pos = text.rfind(marker)
                    if pos != -1:
                        body = text[pos + len(marker):]
                        body = body.replace('\r\n', '\n')
                        newline_count = 0
                        for idx, char in enumerate(body):
                            if char == '\n':
                                newline_count += 1
                            if newline_count == 14:
                                body = body[idx + 1:].strip()
                                break
                        else:
                            body = body.strip() 
                    else:
                        body = text.strip()
                    break
    else:
        try:
            body = msg.get_payload(decode=True).decode("utf-8")
        except Exception as e:
            print(f"Error decoding payload: {e}")

    return body

def get_llm_info(msg,dec=False,ven=False,tim=False):
    ques = {}
    event_details = {}
    ask = False
    if ven:
        ques.update({"venue" : "Where is the event taking place?"})
        ask = True
    if tim:
        ques.update({"time" : "When is the event scheduled?, give in dd-mm-yyyy"})
        ask = True
    event_details = {}
    if ask:
        for key, question in ques.items():
            
            answer = qa_pipeline(question=question, context=msg)
            event_details[key] = answer['answer']
            if key == "time":
                try:
                    event_details[key] = parser.parse(answer['answer'])
                except:
                    event_details[key] = None
    if dec:
        description = summarizer(msg, max_length=60, min_length=20, do_sample=False)[0]['summary_text']
        event_details['description'] = description
    categories = ["meeting", "conference", "seminar", "workshop", "webinar", "lecture","sports","cultural","hackathon","competition","cultural","volunteering","exhibition","ceremony","tournament"]
    category = classifier(msg, candidate_labels=categories)['labels'][0]
    event_details['category'] = category
    return event_details

def get_info(msg):
    subject = get_subject(msg)
    if subject == 'NO':
        return None
    body = get_body(msg)
    email_content = body
    info = {}
    description_pattern = re.compile(
        r"(?:(?:PARTICIPATION INVITATION|INVITATION TO PARTICIPATE|INVITATION|Dear all|Greetings|Dear|Respected).*?)?"
        r"(?:(.+?)(?=\n\n|Thank you|Sincerely|Best regards|Regards|Warm Regards|With Best Wishes|---|--- End of Message ---))",
        re.DOTALL | re.IGNORECASE
    )    
    venue_pattern = re.compile(
        r"(venue|location|place|to be held at|address|event at|hosted at|where):?\s*(.+?)(?=\n|$)",
        re.IGNORECASE
    )
    start_time_pattern = re.compile(
        r"(date|time|when|scheduled on|to occur on|happening on):?\s*"
        r"(\d{2}/\d{2}/\d{4} \d{2}:\d{2}|\d{2}-\d{2}-\d{4} \d{2}:\d{2}|\d{2} \w+ \d{4}(?: at \d{2}:\d{2})?)",
        re.IGNORECASE
    )
    desc, ven, tim = False, False, False
    description = description_pattern.search(email_content)
    if description and description.group(1):
        description = description.group(1).strip() 
        info['description'] = description
    else:
        desc = True        
    venue = venue_pattern.search(email_content)
    if venue and venue.group(2):
        venue = venue.group(2).strip() 
        info['venue'] = venue
    else:
        ven = True
    start_time = start_time_pattern.search(email_content)
    if start_time and start_time.group(2):
        start_time = start_time.group(2).strip()
        try:
            start_time = parser.parse(start_time)
            info['time'] = start_time
        except:
            tim = True
    else:
        tim = True
    info_n = get_llm_info(body,desc,ven,tim)
    info.update(info_n)
    return info

def store(subject,info):
    print(subject,info)
    if Public_Events.query.filter(Public_Events.summary.contains(subject)).first():
        return 
    kolkata_tz = pytz.timezone('Asia/Kolkata')
    if info['time'] == None:
        return
    events = Public_Events.query.all()
    num = get_unique_num(events)
    new_event = Public_Events(
        user_id = "0",
        event_id = str(num),
        summary = subject,
        location = info['venue'],
        description =  info['description'],
        start_time = info['time'].astimezone(kolkata_tz),
        category = info['category']
    ) 
    db.session.add(new_event)
    print("Added event")
    db.session.commit()


if __name__ == '__main__':
    with app.app_context():
        messages = get_status_and_msg()
        print("GOT messages",messages)
        if messages == None:
            exit()
        data = get_emails(messages)
        print("Got emails")
        if len(data) == 0:
            print("len is 0")
            exit()
        for i in range(len(data)):
            print(i)
            msg = BytesParser().parsebytes(data[i][0][1])
            subject = get_subject(msg)
            if Public_Events.query.filter(Public_Events.summary.contains(subject)).first():
                continue
            info = get_info(msg)
            store(subject,info)
