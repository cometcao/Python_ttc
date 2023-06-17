# -*- encoding: utf8 -*-

# 商业转载请联系作者获得授权，非商业转载请注明出处。
# For commercial use, please contact the author for authorization. For non-commercial use, please indicate the source.
# 协议(License)：署名-非商业性使用-相同方式共享 4.0 国际 (CC BY-NC-SA 4.0)
# 作者(Author)：Yaodo
# 链接(URL)：https://www.imtrq.com/archives/2840
# 来源(Source)：Yaodo Blog - 妖渡的博客

import requests, re, os, socket
from bs4 import BeautifulSoup
from urllib.request import urlretrieve
from tqdm import tqdm
import multiprocessing as mp
import datetime

def get_title(key):
    detail_url = 'https://91porny.com/video/view/{0}'.format(key)
    r = requests.get(detail_url)
    soup = BeautifulSoup(r.text, 'lxml')
    title = soup.h4.text
    print('将下载这个视频：{}'.format(title))
    return re.sub('\s','',title)
def make_dir():
    os.chdir(os.path.dirname(__file__))
    if os.path.exists('videos_91'):
        os.system('rd /s /q videos_91')
    os.mkdir('videos_91')
    os.chdir('videos_91')
def get_ts_list(key):
    url = 'https://91porny.com/video/embed/{}'.format(key)
    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'lxml')
    m3u8_url = soup.find('video').get('data-src')
    m3u8 = '/'.join(m3u8_url.split('/')[:-1])
    index = requests.get(m3u8_url).text
    ts_list = re.findall('index.*?ts', index)
    return [(m3u8, i) for i in ts_list]
def downloader(ts):
    ts_url = '{}/{}'.format(ts[0], ts[1])
    urlretrieve(ts_url, ts[1])
def rename_ts(path, ts_list):
    rename_dict = {i[1]:'{}.ts'.format(ts_list.index(i)+1).zfill(8) for i in ts_list}
    for r, ds, fs in os.walk(path):
        for f in fs:
            os.rename(f,rename_dict[f])
def merge_ts(path, title):
    os.chdir('..')
    cwd = os.getcwd()
    cmd = 'copy /b videos_91\*.ts {}.mp4'.format(title)
    os.system(cmd)
    os.system('rd /s /q videos_91')
    input('视频已经存储为 {}\{}.mp4\n请按任意键退出。'.format(cwd, title))
if __name__ == '__main__':
    socket.setdefaulttimeout(20)
    key = input('请输入视频的viewkey：')
    title = get_title(key)
    make_dir()
    ts_list = get_ts_list(key)
    p = mp.Pool()
    for _ in tqdm(p.imap(downloader,ts_list), total=len(ts_list)): pass
    p.close()
    p.join()
    path = os.getcwd()
    rename_ts(path, ts_list)
    merge_ts(path, title)