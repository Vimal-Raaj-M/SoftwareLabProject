from bs4 import BeautifulSoup
import re
from selenium import webdriver
import time
from selenium.webdriver.chrome.options import Options
import dateutil.parser as dparser
from datetime import datetime 

from config import db, app
from models import Event


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

        new_event = Event(
            name = title,
            organizer = "CSE DEPT",
            date = date.date(),
            start_time = date.time(),
            description = "Talk by " + speaker + " on " + title,
            category = "Talks",
            venue = venue
        )
        db.session.add(new_event)
        db.session.commit()

def clear_old_events():
    present = datetime.now()
    current_date = present.date()
    current_time = present.time()

    db.session.query(Event).filter(
        (Event.date < current_date) | ((Event.date == current_date) & (Event.start_time < current_time))
        ).delete(synchronize_session='fetch')

    db.session.commit()

if __name__ == "__main__":
    with app.app_context():
        clear_old_events()
        web_scrape()