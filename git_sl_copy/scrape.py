from bs4 import BeautifulSoup
import re
from selenium import webdriver
import time
from selenium.webdriver.chrome.options import Options
import dateutil.parser as dparser
from datetime import datetime 

from config import db, app
from models import Public_Events

def get_unique_num(events):
    max = 0
    for event in events:
        id = int(event.event_id)
        if id > max:
            max = id
    return max+1


def web_scrape():
    chrome_options = Options()
    chrome_options.add_argument("--headless")  

    url = "https://www.cse.iitb.ac.in/talks"

    driver = webdriver.Chrome()  
    driver.get(url)

    time.sleep(3)  

    html_content = driver.page_source
    driver.quit()
    soup = BeautifulSoup(html_content, 'html.parser')
    present = datetime.now()
    talk_details = []

    talks = soup.find_all('h2', class_='accordion-header')

    for talk in talks:
        title = talk.find('p').get_text(strip=True) if talk.find('p') else "N/A"
        
        speaker = talk.find('span', class_='talk-speaker').get_text(strip=True) if talk.find('span', class_='talk-speaker') else "N/A"
        
        date_time = talk.find_all('span', class_='talk-brief')[0].get_text(strip=True) if talk.find_all('span', class_='talk-brief') else "N/A"
        date = dparser.parse(date_time)
        if date < present:
            continue
        venue = talk.find_all('span', class_='talk-brief')[1].get_text(strip=True) if len(talk.find_all('span', class_='talk-brief')) > 1 else "N/A"
        venue = re.sub(r"^Venue:\s*", "", venue) 
        venue = re.sub(r"\s*\(.*\)$", "", venue)

        talk_info = {
            "title": title,
            "speaker": speaker,
            "date_time": date,
            "venue": venue
        }
        '''
        new_event = Event(
            name = title,
            organizer = "CSE DEPT",
            date = date.date(),
            start_time = date.time(),
            description = "Talk by "+speaker+" on "+title,
            category = "Talks"
        )
        '''
        events = Public_Events.query.all()
        num = get_unique_num(events)
        new_event = Public_Events(
            user_id = "0",
            event_id = str(num),
            summary = title,
            location = venue,
            description =  "Talk by "+speaker+" on "+title,
            start_datetime = date,
            category = 'CSE Dept. Talks'
        )   
        db.session.add(new_event)
        db.session.commit()
        talk_details.append(talk_info)

def clear_old_events():
    present = datetime.now()

    db.session.query(Public_Events).filter(
        (Public_Events.end_datetime < present)
        ).delete(synchronize_session='fetch')

    db.session.commit()

if __name__ == "__main__":
    with app.app_context():
        clear_old_events()
        web_scrape()