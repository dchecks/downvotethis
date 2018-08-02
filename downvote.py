import requests
from requests_html import HTMLSession
from datetime import datetime

import firebase

LOGIN_URL = "https://news.ycombinator.com/login"
ARTICLE_URL = "https://news.ycombinator.com/item?id=%s"
STREAM_API = "https://hacker-news.firebaseio.com/v0/updates.json"
COMMENT_API = "https://hacker-news.firebaseio.com/v0/item/%s.json"
VOTE_URL = "https://news.ycombinator.com/vote?id=%s&how=%s&auth=%s&goto=item%3Fid%3D%s"

VOTE_DIRECTION = "up"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_5) AppleWebKit/537.36 (KHTML, like Gecko) Iridium/2017.11 Safari/537.36 Chrome/62.0.3202.94"

header = {'User-Agent': UA}
auth_cookie = None

session = HTMLSession()
session.headers = header


def vote(comment_id, direction):
    url = ARTICLE_URL % comment_id
    resp = session.get(url)

    for link in resp.html.absolute_links:
        if link.contains("vote?id=%s&how=%s" % (comment_id, direction)):
            vote_url = link

    if not vote_url:
        raise RuntimeError("No vote url found")

    # print("Vote URL: %s" % vote_url)
    vote_resp = session.get(vote_url)
    if vote_resp.is_redirect():
        print("Vote success: %s" % vote_url)
    else:
        print("Vote flailed: HTTP code %s" % vote_resp.status_code)


def check_text(text):
    """Returns true if the text is worthy of a downvote"""
    if not text or len(text) == 0:
        return False

    tmp_text = ''.join(e for e in text if e.isalnum()).lower()
    if tmp_text == 'this':
        return True
    else:
        return False


def login(username, password):
    """Returns the auth cookie as a dictionary from the result of the login form"""
    payload = {'goto': 'news', 'acct': username, 'pw': password}
    response = session.post(LOGIN_URL, data=payload)
    print("Login HTTP status code: %s" % response.status_code)


def check_items(stream_text):
    """Checks a list of item ids for comments and bad text"""
    message = stream_text[1]
    print(datetime.now())
    print('Data: ' + str(message))
    items = message['data']['items']

    for hn_id in items:
        try:
            item_info = requests.get(COMMENT_API % hn_id).json()
            if item_info['type'] == "comment" and check_text(item_info["text"]):
                print("Found comment: %s, text: %s" % (hn_id, item_info['text']))
                vote(hn_id, VOTE_DIRECTION)
        except Exception as e:
            print("Failed to parse item %s" % hn_id)
            print(e)

    print('Checked %s items' % len(items))


login(username='bonzizzle', password='boguspasswd')
if session.cookies.get("user") is None:
    print("Quiting due to lack of auth")
    exit(1)
print("Subscribing to stream")
#subscribe to stream
comment_sub = firebase.subscriber(STREAM_API, check_items)
comment_sub.start()
print("Running...")
