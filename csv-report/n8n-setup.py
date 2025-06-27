import os
import time
from uuid import uuid4
import logging
import json
import httpx
import backoff

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

N8N_URL = os.getenv('N8N_URL', 'http://localhost:5678')
N8N_EMAIL = os.getenv('N8N_EMAIL', 'dev@localhost.com')
N8N_PASSWORD = os.getenv('N8N_PASSWORD', 'Dev12345678')
OPEN_AI_API_KEY = os.getenv('OPEN_AI_API_KEY')


class N8NSetup:
    def __init__(self):

        self.project_id = None

        self.headers = {
            'browser-id': str(uuid4())
        }

    @staticmethod
    def wait_until_online():
        while True:
            try:
                r = httpx.get(f'{N8N_URL}/healthz')

                if r.status_code == 200:
                    logger.info('N8N is online and ready to setup')
                    break
                else:
                    logger.info('N8N is offline')
            except Exception as ex:
                logger.info(str(ex))

            time.sleep(3)

    @backoff.on_exception(backoff.constant, Exception, interval=1, max_tries=5)
    def create_owner_account(self):
        r = httpx.post(
            f'{N8N_URL}/rest/owner/setup',
            json={
                'email': N8N_EMAIL,
                'firstName': 'dev',
                'lastName': 'dev',
                'password': N8N_PASSWORD
            }
        )

        if r.status_code == 200:
            logger.info('Owner user account created successfully')
        else:
            if 'Instance owner already setup' in r.text:
                logger.info('Owner user account already setup')
            else:
                raise Exception('Failed to create owner account')

    @backoff.on_exception(backoff.constant, Exception, interval=1, max_tries=5)
    def login(self):
        r = httpx.post(
            f'{N8N_URL}/rest/login',
            json={
                'emailOrLdapLoginId': N8N_EMAIL,
                'password': N8N_PASSWORD
            },
            headers=self.headers
        )

        if r.status_code == 200:
            logger.info('User login successful')
        else:
            raise Exception('Failed to login user')

        auth_token = r.cookies.get('n8n-auth')

        self.headers.update({
            'Cookie': f'n8n-auth={auth_token}'
        })

        r = httpx.get(
            f'{N8N_URL}/rest/projects/my-projects',
            headers=self.headers
        )

        if r.status_code == 200:
            self.project_id = r.json()['data'][0]['id']
        else:
            raise Exception('Failed to get project id')

    @backoff.on_exception(backoff.constant, Exception, interval=1, max_tries=5)
    def set_survey(self):

        r = httpx.post(
            f'{N8N_URL}/rest/me/survey',
            json={
                'companyType': 'saas',
                'role': 'business-owner',
                'automationBeneficiary': 'myself',
                'companySize': '<20',
                'reportedSource': 'google',
                'version': 'v4',
                'personalization_survey_submitted_at': '2025-06-25T04:39:52.628Z',
                'personalization_survey_n8n_version': '1.99.1'
            },
            headers=self.headers
        )

        if r.status_code == 200:
            logger.info('Survey set successful')
        else:
            raise Exception('Failed to set survey')

    @backoff.on_exception(backoff.constant, Exception, interval=1, max_tries=5)
    def _get_credentials(self) -> list[str]:
        r = httpx.get(
            f'{N8N_URL}/rest/credentials?includeScopes=true&includeData=true&filter=%7B%22projectId%22%3A%22{self.project_id}%22%7D',
            headers=self.headers
        )

        if r.status_code == 200:
            return [i['name'] for i in r.json()['data']]
        else:
            raise Exception('Failed to get credentials')

    @backoff.on_exception(backoff.constant, Exception, interval=1, max_tries=5)
    def create_credential(self, data: dict) -> str | None:

        credentials_names = self._get_credentials()

        if data['name'] in credentials_names:
            return None

        data['projectId'] = self.project_id

        r = httpx.post(
            f'{N8N_URL}/rest/credentials',
            json=data,
            headers=self.headers
        )

        if r.status_code == 200:
            c_id = r.json()['data']['id']
            logger.info(f'Credential {data['name']} created successfully')
        else:
            raise Exception('Failed to create credential')

        data['id'] = c_id

        r = httpx.post(
            f'{N8N_URL}/rest/credentials/test',
            json={
                'credentials': data
            },
            headers=self.headers
        )

        if r.status_code == 200:
            logger.info(f'Credential {data['name']} tested successfully')
        else:
            raise Exception('Failed to test credential')

        return c_id

    @backoff.on_exception(backoff.constant, Exception, interval=1, max_tries=5)
    def create_workflow(self, data: dict):
        r = httpx.post(
            f'{N8N_URL}/rest/workflows',
            json=data,
            headers=self.headers
        )

        if r.status_code == 200:
            logger.info(f"Workflow {data['name']} created successfully")
        else:
            raise Exception('Failed to create workflow')

    @backoff.on_exception(backoff.constant, Exception, interval=1, max_tries=5)
    def get_workflow_names(self) -> list[str] | None:
        r = httpx.get(
            f'{N8N_URL}/rest/workflows?includeScopes=true&filter=%7B%22isArchived%22%3Afalse%7D&skip=0&take=50&sortBy=updatedAt%3Adesc',
            headers=self.headers
        )

        names = []

        if r.status_code == 200:
            for i in r.json()['data']:
                names.append(i['name'])

        return names


n8n = N8NSetup()

n8n.wait_until_online()
n8n.create_owner_account()
n8n.login()
n8n.set_survey()

smtp_crd_id = n8n.create_credential(data={
    'name': 'SMTP MailHog',
    'type': 'smtp',
    'data': {
        'host': 'mailhog',
        'port': 1025,
        'secure': False
    }
})

postgres_crd_id = n8n.create_credential(data={
    'name': 'Outlet DB',
    'type': 'postgres',
    'data': {
        'host': 'outlet-db',
        'database': 'outlet',
        'user': 'dev',
        'password': 'dev'
    }
})

open_ai_crd_id = n8n.create_credential(data={
    'name': 'OpenAI Account',
    'type': 'openAiApi',
    'data': {
        'apiKey': OPEN_AI_API_KEY,
        'url': 'https://api.openai.com/v1'
    }
})

with open('/tmp/workflows/csv_report.json', 'r') as file:
    data = json.load(file)

    for node in data['nodes']:
        if node.get('credentials', {}).get('postgres', {}).get('name') == 'Outlet DB':
            node['credentials']['postgres']['id'] = postgres_crd_id
        elif node.get('credentials', {}).get('openAiApi', {}).get('name') == 'OpenAI Account':
            node['credentials']['openAiApi']['id'] = open_ai_crd_id
        elif node.get('credentials', {}).get('smtp', {}).get('name') == 'SMTP MailHog':
            node['credentials']['smtp']['id'] = smtp_crd_id

    workflow_name = data.get('name')
    workflows_names = n8n.get_workflow_names()

    if workflow_name not in workflows_names:
        n8n.create_workflow(data=data)

logger.info('N8N setup successfully')
