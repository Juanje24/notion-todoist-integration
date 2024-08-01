import requests

# tokens & id's - see the readme.md file for where to find these
TODOIST_API_TOKEN = ""
NOTION_API_TOKEN = ""
NOTION_DATABASE_ID = ""
TODOIST_INBOX_PROJECT_ID = ""  

# fetching tasks from todoist
def get_todoist_tasks():
    url = f"https://api.todoist.com/rest/v2/tasks?project_id={TODOIST_INBOX_PROJECT_ID}"
    headers = {
        "Authorization": f"Bearer {TODOIST_API_TOKEN}"
    }
    response = requests.get(url, headers=headers)

    # otherwise raise an error 
    response.raise_for_status()  

    # returns the the list of tasks
    return response.json()

# fetching the tasks from notion (this is needed to compare the tasks in notion vs todoist)
def get_notion_tasks():
    url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"
    headers = {
        "Authorization": f"Bearer {NOTION_API_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    response = requests.post(url, headers=headers)

    # otherwise raise an error
    response.raise_for_status()  

    # return the list of tasks
    return response.json()

# add task to notion
def add_task_to_notion(task):
    url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {NOTION_API_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"  # this is not the version of notion that you are on, but rather the api version -see the readme file for more 
    }


    # fetch the due date, if there is no due date, then we leave that field blank
    due_date = task.get("due")
    start_date = due_date.get("date") if due_date else None
    
    # fetching for the due date in todoist returns a date that looks looks like something like this (ex): 2019-12-11T22:36:50.000000Z
    # we don't want that, so we split it ito date and time, and take just the date portion
    # that leaves us with 2019-12-11 (for example)
    if start_date:
        start_date = start_date.split('T')[0]  # Extract date only

    # crate new task properties for otion
    properties = {
        "Task Name": {
            "title": [
                {
                    "text": {
                        "content": task["content"]
                    }
                }
            ]
        },
        "Description": {
            "rich_text": [
                {
                    "text": {
                        "content": task.get("description", "")
                    }
                }
            ]
        }
    }

    # we can only add the due date for the task if the date exists, checking for that 
    if start_date:
        properties["Due Date"] = {
            "date": {
                "start": start_date
            }
        }

    # the database to which we want to send it
    data = {
        "parent": {"database_id": NOTION_DATABASE_ID},
        "properties": properties
    }

    # information that will show up in the cmd prompt when running teh script
    print("Sending request data:", data)  # Debug: Check the request data


    # return the result, otherwise print an error
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()  
    return response.json()


# run the script
def main():
    try:
        todoist_tasks = get_todoist_tasks()
        notion_tasks = get_notion_tasks()


        # we need to check if the task already exists or not
        notion_task_titles = set(
            item["properties"]["Task Name"]["title"][0]["text"]["content"]
            for item in notion_tasks["results"]
        )

        # new tasks are one that are not currently in notion_task_titls
        new_tasks = [task for task in todoist_tasks if task["content"] not in notion_task_titles]

        # so we oly add those
        for task in new_tasks:
            result = add_task_to_notion(task)
            print(f"Added task to Notion: {result}")


    # errors
    except requests.RequestException as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
