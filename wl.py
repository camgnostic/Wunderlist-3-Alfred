from wl_utils import getLists, getListId, refreshTasks, refreshLists, getTasks, getTask
from wl_utils import ICON_ADDTASK, ICON_DELETE, ICON_DONE, ICON_EMPTY, ICON_ITEM, ICON_LIST, ICON_NEWLIST, ICON_STAR, ICON_UNSTAR, ICON_UPDATE
from workflow import Workflow, PasswordNotFound
from workflow.background import is_running
import sys
import threading

def main(wf):
    #if no args, no query:
    if len(wf.args):
        query = u' '.join(wf.args[0:])
        wf.logger.debug(query)
    else:
        query = ""
    try:
        #do we have a login?  If not drop to catch at bottom no api password:
        token = wf.get_password('token')
        add = False
        new = False
        #if add task, strip add and collect listname:
        listId = False
        if query[0:4].lower() == "add:":
            query = query[3:].lstrip(' ').lstrip(":").lstrip(' ')
            if len(query.split(":")) > 1:
                listname = query.split(":")[0]
                listId = getListId(wf, listname)
                query = ":".join(query.split(":")[1:]).lstrip(' ').lstrip(":")
                if listId == False:
                    if not is_running("updateLists"):
                        refreshLists(wf)
                    wf.add_item("List not found, updating lists...", valid=False, icon=ICON_UPDATE)
                else:
                    valid = True if query != "" else False
                    wf.add_item(title = u'' + (query if query != "" else 'New Task'),
                                subtitle = u'add to list: ' + str(listname),
                                valid=valid, arg='add:' + str(listId) + ':' + str(query),
                                icon = ICON_ADDTASK)
                wf.send_feedback()
            add = True
            wf.add_item(title = u'Add an item to the highlighted list:',
                        valid=False, icon=ICON_ADDTASK)
            getLists(wf, query, True)
        #if new list, strip new and collect new listname:
        elif query[0:4].lower() == "new:":
            query = query[3:].lstrip(' ').lstrip(":").lstrip(' ')
            new = True
            valid = True if query != "" else False
            wf.add_item(title = u'' + query,
                        subtitle='add new list',
                        valid=valid, arg='new:' + query,
                        icon=ICON_NEWLIST)
            wf.send_feedback()
        if len(query.split(":")) > 1:
            listname = query.split(":")[0]
            listId = getListId(wf, listname)
            query = ":".join(query.split(":")[1:]).lstrip(' ').lstrip(':')
            #listname not found:
            if listId == False:
                if not is_running("updateLists"):
                    refreshLists(wf)
                wf.add_item("List not found, updating lists...", valid=False, icon=ICON_UPDATE)
                wf.send_feedback()
            #listname found, is taskname found?
            elif getTask(wf, listId, query):
                task = getTask(wf, listId, query)
                taskId = task['id']
                query = ":".join(query.split(":")[1:]).lstrip(' ').lstrip(":")
                #taskname not found:
                if taskId == False:
                    if not is_running("updateTasks:" + str(listId)):
                        refreshTasks(wf, listId)
                    wf.add_item("Task not found, updating tasks....", valid=False, icon=ICON_UPDATE)
                    wf.send_feedback()
                #taskname found. tasks menu
                else:
                    wf.add_item(title = u'' + listname + ':' + task['title'] + ':', valid=False,
                                icon=(ICON_STAR if task['starred'] else ICON_ITEM))
                    wf.add_item(title = u'Mark as Complete', subtitle = u'Task will not show in list when marked complete',
                                valid=True, arg="done:" + str(listId) + ":" + str(taskId),
                                icon=ICON_DONE)
                    wf.add_item(title = u'' + ("Uns" if task['starred'] == True else "S") + "tar task",
                                valid=True, arg="star:" + str(listId) + ":" + str(taskId),
                                icon=(ICON_UNSTAR if task['starred'] else ICON_STAR))
                    wf.add_item(title = u'Delete task', subtitle='This will permanently delete this task',
                                valid=True, arg="rem:" + str(listId) + ":" + str(taskId),
                                icon = ICON_DELETE)
                    wf.send_feedback()
            elif add == False:
                getTasks(wf, listId, listname, query)
                
        #not new or add, still searching lists:
        if new == False and add == False and not listId:
            if query == "":
                wf.add_item(title = u'Add', subtitle = u'Add a new task to a list',
                            valid=False, autocomplete="Add:", icon=ICON_ADDTASK)
                wf.add_item(title = u'New', subtitle = u'New list',
                            valid=False, autocomplete="New:", icon=ICON_NEWLIST)
            getLists(wf, query)
            
    except PasswordNotFound:
        wf.add_item(title = u'Login', subtitle = u'Authorize with Wunderlist',
                    arg = "login", valid=True, icon=ICON_EMPTY)

    
    
if __name__ == '__main__':
    wf = Workflow()
    sys.exit(wf.run(main))
    