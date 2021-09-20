# /path/to/server.py
from jinja2 import Environment, FileSystemLoader
from datetime import datetime, timedelta
from urllib.parse import unquote

from sanic.response import redirect
from sanic.response import text
from sanic.response import html
from sanic import Sanic

from bs4 import BeautifulSoup
from random import randrange
import ruamel.yaml
import datetime
import os.path
import httpx
import qrcode
import os
import re

#import git
import time

base_dir = os.path.abspath(os.path.dirname(__name__))
static_dir = os.path.join(base_dir, 'static')
templates_dir = os.path.join(base_dir, 'templates')
data_dir = os.path.join(base_dir, 'data')
env = Environment(loader=FileSystemLoader(templates_dir), autoescape=True)

app = Sanic(__name__)
app.static('/static', static_dir)

yaml = ruamel.yaml.YAML()

# filename = ""
@app.route("/", name="index")
@app.route("/index", name="index")
async def index(request):
    template = env.get_template('index.html')
    with open(f"{data_dir}/exchanges.yml", "r") as exchanges:
        data = yaml.load(exchanges)
        data['exchanges'] = sorted(data['exchanges'], key=lambda k: k['score'], reverse=True)
        return html(template.render(date=date, data=data,
                                    title="KYC? Not me!",
                                    subtitle="Find best <strong>NON-KYC</strong> online services."))


@app.route("/services", name="services")
async def services(request):
    template = env.get_template('services.html')
    with open(f"{data_dir}/services.yml", "r") as services:
        data = yaml.load(services)
        data['services'] = sorted(data['services'], key=lambda k: k['category'], reverse=True)
        return html(template.render(date=date, data=data,
                                    title="KYC? Not me!",
                                    subtitle="Find best <strong>NON-KYC</strong> online services."))


@app.route("/about", name="about")
async def about(request):
    template = env.get_template('about.html')
    r = httpx.get(
        "https://codeberg.org/schylza/schylza/raw/branch/main/SUPPORT.md")
    donations = yaml.load(r.content)
    return html(template.render(date=date, title="KYC? Not me!",
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
                    return html(template.render(date=date, exchange=exchange, title="KYC? Not me!", color=color))
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
                    return html(template.render(date=date, service=service, tpinfo=tpinfo))
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
          suspicious-tos: false
          refunds: false
          score: 6
          tor: {args['tor'][0]}
          tor-url: {args['tor-url'][0]}
          tos-urls:
          - {args['tos'][0]}
          url: {args['url'][0]}
          verified: false
          score-boost: 0 </pre>
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
          category: {args['category'][0]}
          verified: false</pre>
        """
        return(html(yamlString))
    template = env.get_template('generate-new-service.html')
    if(request.json):
        return text('POST request - {}'.format(request.json))
    return(html(template.render()))

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

'''def get_last_commit_date():
    repo = git.Repo(search_parent_directories=True)
    tree = repo.tree()
    lastcommit = 1111316191
    for blob in tree:
        commit = list(repo.iter_commits(paths=blob.path, max_count=1))
        date = commit[0].committed_date
        if lastcommit < date:
            lastcommit = date
    return time.strftime("%d/%m/%Y", time.gmtime(date))

date = get_last_commit_date()'''
date = "13/09/21"