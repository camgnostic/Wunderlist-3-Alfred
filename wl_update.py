from lib import requests
import sys
import json
from workflow import Workflow, web, PasswordNotFound

api_url = "https://a.wunderlist.com/api/v1/"

class Updater(object):
    def __init__(self, wf):
        self.wf = wf
        if len(wf.args):
            query = wf.args[0]
        try:
            self.token = wf.get_password('token')
        except PasswordNotFound:
            wf.logger.warning('no api key set')
        else:
            self.headers = {"X-Access-Token": self.token,
                            "X-Client-ID": wf.settings['api']['client_id'],
                            'content-type': 'application/json'}
            if query == "lists":
                lists = wf.cached_data('lists', self.updateLists, max_age=600)
                positions = wf.cached_data('positions', self.updateListPositions, max_age=600)
                for list_id in lists.keys():
                    self.listId = list_id
                    counts = wf.cached_data('counts:' + self.listId, self.updateCounts, max_age=600)
                wf.logger.debug('%s lists cached, %s positions cached' % (len(lists), len(positions)))
            if len(query.split(":")) > 1:
                if query.split(":")[0] == "tasks":
                    self.listId = query.split(":")[1]
                    tasks = wf.cached_data('tasks:' + self.listId,
                                               self.updateTasks, max_age=600)
                    task_positions = wf.cached_data('task_positions:' + self.listId,
                                                        self.updateTaskPositions,
                                                        max_age=600)
                    wf.logger.debug('{} tasks cached, {} positions cached, listID: {}'.format(len(tasks),
                                                                                              len(task_positions),
                                                                                              self.listId))
            
    def updateLists(self):
        url = api_url + "lists"
        r = web.get(url, headers=self.headers)
        r.raise_for_status()
        lists = {}
        for l in r.json():
            lists[str(l['id'])] = l
        return lists
    
    def updateListPositions(self):
        url = api_url + "list_positions"
        r = web.get(url, headers=self.headers)
        r.raise_for_status()
        positions = r.json()[0]['values']
        return positions
    
    def updateCounts(self):
        url = api_url + "lists/tasks_count?list_id=" + self.listId
        r = web.get(url, headers=self.headers)
        r.raise_for_status()
        data = r.json()
        counts = (data['completed_count'], data['uncompleted_count'])
        return counts
        
    def updateTasks(self):
        url = api_url + "tasks?list_id=" + self.listId
        r = web.get(url, headers=self.headers)
        r.raise_for_status()
        tasks = {}
        for t in r.json():
            tasks[str(t['id'])] = t
        return tasks
    
    def updateTaskPositions(self):
        url = api_url + "task_positions?list_id=" + self.listId
        r = web.get(url, headers=self.headers)
        r.raise_for_status()
        task_positions = r.json()[0]['values']
        return task_positions
    

def main(wf):
    u = Updater(wf)
        
if __name__ == '__main__':
    wf = Workflow()
    wf.run(main)
