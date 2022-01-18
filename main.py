import requests
from bs4 import BeautifulSoup
headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/52.0.2743.82 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Upgrade-Insecure-Requests': '1',
            'Cookie': "ipb_member_id=5774855; ipb_pass_hash=4b061c3abe25289568b5a8e0123fb3b9; igneous=cea2e08fb; "
                      "sk=oye107wk02gtomb56x65dmv4qzbn; u=5774855-0-qc5eog69s0z"}
session = requests.session()
content = session.get("https://exhentai.org/s/3eaeae6d2e/2093300-1", headers=headers).content
soup = BeautifulSoup(content, "html.parser")
img = soup.find('div', id='i3').find('img', id='img')['src']
print(img)
content = session.get(img, headers=headers).content
with open("test.jpg", 'wb') as file:
    file.write(content)