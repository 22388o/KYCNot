# /path/to/server.py
from jinja2 import Environment, FileSystemLoader
from datetime import datetime, timedelta
from urllib.parse import unquote

from sanic.response import redirect
from sanic.response import text
from sanic.response import html
from sanic import Sanic

import ruamel.yaml
from bs4 import BeautifulSoup
from random import randrange
import datetime
import os.path
import httpx
import os
import re

base_dir = os.path.abspath(os.path.dirname(__name__))
static_dir = os.path.join(base_dir, 'static')
templates_dir = os.path.join(base_dir, 'templates')
data_dir = os.path.join(base_dir, 'data')
env = Environment(loader=FileSystemLoader(templates_dir), autoescape=True)
app = Sanic(__name__)
yaml = ruamel.yaml.YAML()

app.static('/static', static_dir)

FOOTER = f"""<footer class="container">
<pre>by <a href="https://github.com/pluja">Pluja</a>.</pre> <br>
    <b style="font-size:.6em; color:#FB8537;"> <img style="width:2%;" src="https://web.getmonero.org/press-kit/symbols/monero-symbol-480.png"><mark>xmr:</mark> 83czvTQL5cHXZZpRM6bvcqVZSbNRqsX1tMwWnx1HjKBUD8swxUm9fFiTHUZbfYg8qPLM4nLwSdGCM1JmAXUp886KG93Pccr</b><br>
    <b style="font-size:.6em; color:#1372A4;"> <mark>Ł (ltc):</mark> MMSW3AnzHbxnmVeXzGjnNgHf6h62qpR9VA</b></br>
    <b style="font-size:.6em; color:#FEAC48;"> <mark>₿ (btc):</mark> bc1qnrh67j3q0y8kzsxl9npgrlqhalcgx4awa3j2u0</b><br>
</footer>"""

"""
# is-primary = Teal -> Verified tag
# is-success = Green -> Positive
# is-warning = Yellow -> Warning
# is-danger = Red -> Negative / Danger
# is-black = Black -> Other info
# is-light = Dark Grey -> None
# is-info = Info Blue -> Buy/Exchange
# is-dark = Light grey -> XMR / BTC non accepted
"""

# filename = ""


@app.route("/", name="index")
@app.route("/index", name="index")
async def index(request):
    template = env.get_template('index.html')
    with open(f"{data_dir}/exchanges.yml", "r") as exchanges:
        data = yaml.load(exchanges)
        # Run check every 3 days
        if (data['last_check'] + datetime.timedelta(days=3)) < datetime.datetime.today():
            # await kyc_check()
            await compute_score()
        return html(template.render(data=data,
                                    title="KYC? Not me!",
                                    subtitle="Find best <strong>NON-KYC</strong> online services."))


@app.route("/services", name="services")
async def services(request):
    template = env.get_template('services.html')
    with open(f"{data_dir}/services.yml", "r") as services:
        data = yaml.load(services)
        return html(template.render(data=data,
                                    title="KYC? Not me!",
                                    subtitle="Find best <strong>NON-KYC</strong> online services."))


@app.route("/about", name="about")
async def about(request):
    template = env.get_template('about.html')
    r = httpx.get(
        "https://codeberg.org/schylza/schylza/raw/branch/main/SUPPORT.md")
    donations = yaml.load(r.content)
    return html(template.render(title="KYC? Not me!",
                                subtitle="About KYCNOT.ME",
                                support=donations))


@app.route("/exchange/<name>")
async def exchange(request, name=None):
    if(name):
        with open(f"{data_dir}/exchanges.yml", "r") as exchanges:
            data = yaml.load(exchanges)
            for exchange in data['exchanges']:
                if ''.join(exchange['name'].split()).lower() == name:
                    template = env.get_template('exchange.html')
                    if exchange['score'] > 7:
                        color = "#18B432"
                    elif exchange['score'] <= 7 and exchange['score'] >= 5:
                        color = "#FFB800"
                    else:
                        color = "#a71d31"
                    return html(template.render(exchange=exchange, title="KYC? Not me!", color=color))
    return(f"{name} does not exist")


@app.route("/service/<name>")
async def service(request, name=None):
    if(name):
        with open(f"{data_dir}/services.yml", "r") as services:
            data = yaml.load(services)
            for service in data['services']:
                if service['name'].replace(' ', '').lower() == name:
                    tpinfo = await get_trustpilot_info(service)
                    template = env.get_template('service.html')
                    return html(template.render(service=service, tpinfo=tpinfo))
    return(f"{name} does not exist")


@app.route("/generate-new-exchange", name="new-exchange", methods=['POST', 'GET'])
async def gne(request):
    if(request.args):
        args = request.args
        yamlString = f"""
        <pre>- name: {args['name'][0]}
          short-description: {args['short-d'][0]}
          long-description: {args['large-d'][0]}
          btc: {args['btc'][0]}
          xmr: {args['xmr'][0]}
          cash: {args['cash'][0]}
          exchange: {args['exchange'][0]}
          buy: {args['buy'][0]}
          custodial: {args['custodial'][0]}
          registration: {args['registration'][0]}
          personal-info: {args['personal-info'][0]}
          p2p: {args['p2p'][0]}
          may-kyc: false
          open-source: {args['open-source'][0]}
          comment:
          kyc-check: false
          refunds: false
          rgb-color: 0,213,36
          score: 6
          tor: {args['tor'][0]}
          tor-url: {args['tor-url'][0]}
          tos-urls:
          - {args['tos'][0]}
          url: {args['url'][0]}
          verified: false</pre>
        """
        return(html(yamlString))
    template = env.get_template('generate-new-exchange.html')
    if(request.json):
        return text('POST request - {}'.format(request.json))
    return(html(template.render()))


@app.route("/generate-new-service", name="new-service", methods=['POST', 'GET'])
async def gns(request):
    if(request.args):
        args = request.args
        yamlString = f"""
        <pre>- name: {args['name'][0]}
          short-description: {args['short-d'][0]}
          long-description: {args['large-d'][0]}
          btc: {args['btc'][0]}
          xmr: {args['xmr'][0]}
          cash: {args['cash'][0]}
          registration: {args['registration'][0]}
          personal-info: {args['personal-info'][0]}
          open-source: {args['open-source'][0]}
          tor: {args['tor'][0]}
          tor-url: {args['tor-url'][0]}
          tos-url: {args['tos'][0]}
          url: {args['url'][0]}
          verified: false</pre>
        """
        return(html(yamlString))
    template = env.get_template('generate-new-service.html')
    if(request.json):
        return text('POST request - {}'.format(request.json))
    return(html(template.render()))


async def compute_score():
    with open(f"{data_dir}/exchanges.yml", "r+") as exchanges:
        data = yaml.load(exchanges)
        for exchange in data['exchanges']:
            score = 0
            if not exchange['may-kyc']:
                score += 2.25
            if not exchange['custodial']:
                score += 1.0
            if not exchange['registration']:
                score += 0.75
            if not exchange['personal-info']:
                score += 2.5
            if exchange['kyc-check']:
                score += 1.75
            if exchange['p2p']:
                score += 1.25
            if exchange['open-source']:
                score += 0.25
            if exchange['tor']:
                score += 0.25
            if score < 7 and exchange['verified']:
                score += 1
            if score < 6 and exchange['refunds']:
                score += 1
            if score > 10:
                exchange['score'] = 10.0
            else:
                exchange['score'] = score+exchange['score-boost']
        exchanges.seek(0)
        yaml.dump(data, exchanges)
        exchanges.truncate()


async def kyc_check():
    keywords = ['kyc', 'aml', 'know your customer', 'money laundering', 'terrorist financing', 'identify user', 'user identification', 'User Identity Verification', 'identity verification', 'user identity', 'provide required personal information', 'provide personal information',
                'KYC requirements', 'AML requirements', 'AML/KYC', 'KYC/AML', 'anti-money laundering', 'U.S. Bank Secrecy Act', 'BSA', '4th AML Directive', 'verify your identity', 'passport', "dirver's license", 'identity card', 'verify your identity', 'identity checks', 'mandatory identification', 'complete our ID verification process']
    with open(f"{data_dir}/exchanges.yml", "r+") as exchanges:
        data = yaml.load(exchanges)
        for exchange in data['exchanges']:
            if exchange['tos-urls'][0]:
                for url in exchange['tos-urls']:
                    r = httpx.get(url)
                    pageString = str(BeautifulSoup(
                        r.content, features="html.parser"))
                    fw = []
                    potential_kyc = False
                    foundkw = 0
                    for kw in keywords:
                        if kw in pageString:
                            foundkw += 1
                            fw.append(kw)
                    if foundkw >= 3:
                        potential_kyc = True
            else:
                if ".onion" or "tradeogre" in exchange['url']:
                    potential_kyc = False

            if potential_kyc:
                exchange['kyc-check'] = fw
                exchanges.seek(0)
                yaml.dump(data, exchanges)
                exchanges.truncate()
                print("------ WARNING ------")
                print(
                    f''' Potential KYC on {exchange['name']} ToS. Found words were: \n {fw}''')
                print("---------------------")
            else:
                exchange['kyc-check'] = True
                exchanges.seek(0)
                yaml.dump(data, exchanges)
                exchanges.truncate()

        data['last_check'] = datetime.datetime.today()
        exchanges.seek(0)
        yaml.dump(data, exchanges)
        exchanges.truncate()


async def get_trustpilot_info(service):
    r = httpx.get(
        f"https://www.trustpilot.com/review/{service['url'].replace('https://', '')[:-1]}")
    soup = BeautifulSoup(r.content, features="html.parser")
    if soup.find_all('div', class_="error-page"):
        trustscore = False
        review_count = ''
        tplink = "#"
    else:
        trustscore = soup.find_all('p', class_='header_trustscore')[0].text
        review_count = soup.find_all(
            'span', class_="headline__review-count")[0].text
        tplink = f"https://www.trustpilot.com/review/{service['url'].replace('https://', '')[:-1]}"
    tpinfo = {
        'score': trustscore,
        'count': review_count,
        'link': tplink
    }
    return tpinfo
