import requests
import os


# Solo carga .env si estás trabajando localmente
if os.getenv("GITHUB_ACTIONS") != "true":
    from dotenv import load_dotenv
    load_dotenv()




# tokens & id's - see the readme.md file for where to find these
TODOIST_API_TOKEN = os.getenv("TODOIST_API_TOKEN")
NOTION_API_TOKEN = os.getenv("NOTION_API_TOKEN")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
TODOIST_INBOX_PROJECT_ID = os.getenv("TODOIST_INBOX_PROJECT_ID")

# fetching tasks from todoist
def get_todoist_tasks():
    url = f"https://api.todoist.com/rest/v2/tasks?project_id={TODOIST_INBOX_PROJECT_ID}"
    headers = {
        "Authorization": f"Bearer {TODOIST_API_TOKEN}"
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()  
    return response.json()

# fetching the tasks from notion (this is needed to compare the tasks in notion vs todoist)
def get_notion_tasks():
    url = f"https://api.notion.com/v1/data_sources/{NOTION_DATABASE_ID}"
    headers = {
        "Authorization": f"Bearer {NOTION_API_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    response = requests.post(url, headers=headers)
    response.raise_for_status()  
    return response.json()

def map_todoist_to_notion_properties(task):
    """
    Mapea los datos de una tarea de Todoist a las propiedades usadas en Notion.
    """
    # Extraer y formatear la fecha de vencimiento
    due_date = task.get("due")
    start_date = due_date.get("date") if due_date else None
    # No hacer split, así se conserva la hora si existe

    # Mapeo de la prioridad (Todoist: 1=más baja, 4=más alta)
    todoist_priority = task.get("priority", 1)
    notion_priority = str(5 - todoist_priority)

    # Obtener tag: si no existe "tag", se usa "labels" en su lugar
    tag = task.get("tag")
    if not tag:
        labels = task.get("labels")
        if labels:
            tag = ", ".join(map(str, labels))
        else:
            tag = ""

    properties = {
        "Task Name": task["content"],
        "Description": task.get("description", ""),
        "Prioridad": notion_priority,
        "Tag": tag,
        "Due Date": start_date  # Puede ser None, pero ahora incluye hora si existe
    }
    return properties

def extract_notion_properties(notion_item):
    """
    Extrae las propiedades relevantes de una tarea en Notion para compararlas.
    """
    props = {}
    # Título
    title_list = notion_item["properties"]["Task Name"].get("title", [])
    props["Task Name"] = title_list[0]["text"]["content"] if title_list else ""
    
    # Descripción
    rich_text_list = notion_item["properties"]["Description"].get("rich_text", [])
    props["Description"] = rich_text_list[0]["text"]["content"] if rich_text_list else ""
    
    # Prioridad
    select_prop = notion_item["properties"]["Prioridad"].get("select")
    props["Prioridad"] = select_prop["name"] if select_prop else ""
    
    # Tag
    tag_list = notion_item["properties"]["Tag"].get("rich_text", [])
    props["Tag"] = tag_list[0]["text"]["content"] if tag_list else ""
    
    # Due Date
    date_prop = notion_item["properties"].get("Due Date", {}).get("date")
    props["Due Date"] = date_prop["start"] if date_prop and date_prop.get("start") else None
    
    return props

def task_needs_update(todoist_task, notion_item):
    """
    Compara la tarea de Todoist con la existente en Notion. Retorna True si hay diferencias.
    """
    todoist_props = map_todoist_to_notion_properties(todoist_task)
    notion_props = extract_notion_properties(notion_item)
    
    # Compara cada campo. Si alguno difiere, se requiere actualizar.
    for key in ["Task Name", "Description", "Prioridad", "Tag", "Due Date"]:
        if todoist_props.get(key) != notion_props.get(key):
            print(f"Diferencia en '{key}': Todoist tiene '{todoist_props.get(key)}' y Notion '{notion_props.get(key)}'")
            return True
    return False

# add task to notion
def add_task_to_notion(task):
    url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {NOTION_API_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    props = map_todoist_to_notion_properties(task)
    
    # Construir las propiedades para la petición
    properties = {
        "Task Name": {
            "title": [
                {
                    "text": {
                        "content": props["Task Name"]
                    }
                }
            ]
        },
        "Description": {
            "rich_text": [
                {
                    "text": {
                        "content": props["Description"]
                    }
                }
            ]
        },
        "Prioridad": {
            "select": {
                "name": props["Prioridad"]
            }
        },
        "Tag": {
            "rich_text": [
                {
                    "text": {
                        "content": props["Tag"]
                    }
                }
            ]
        }
    }
    
    if props["Due Date"]:
        properties["Due Date"] = {
            "date": {
                "start": props["Due Date"]
            }
        }
    
    data = {
        "parent": {"database_id": NOTION_DATABASE_ID},
        "properties": properties
    }
    
    print("Enviando datos para crear tarea:", data)
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()

# update an existing task in Notion
def update_task_in_notion(page_id, task):
    url = f"https://api.notion.com/v1/pages/{page_id}"
    headers = {
        "Authorization": f"Bearer {NOTION_API_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    props = map_todoist_to_notion_properties(task)
    
    properties = {
        "Task Name": {
            "title": [
                {
                    "text": {
                        "content": props["Task Name"]
                    }
                }
            ]
        },
        "Description": {
            "rich_text": [
                {
                    "text": {
                        "content": props["Description"]
                    }
                }
            ]
        },
        "Prioridad": {
            "select": {
                "name": props["Prioridad"]
            }
        },
        "Tag": {
            "rich_text": [
                {
                    "text": {
                        "content": props["Tag"]
                    }
                }
            ]
        }
    }
    
    if props["Due Date"]:
        properties["Due Date"] = {
            "date": {
                "start": props["Due Date"]
            }
        }
    
    data = {
        "properties": properties
    }
    
    print("Enviando datos para actualizar tarea:", data)
    response = requests.patch(url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()

# delete (archive) task in Notion
def delete_task_in_notion(page_id):
    """
    La API de Notion no permite eliminar páginas de forma definitiva,
    pero se puede 'archivar' la página estableciendo el flag 'archived' a True.
    """
    url = f"https://api.notion.com/v1/pages/{page_id}"
    headers = {
        "Authorization": f"Bearer {NOTION_API_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    data = {
        "archived": True
    }
    
    print(f"Archivando la tarea en Notion con page id: {page_id}")
    response = requests.patch(url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()

# run the script
def main():
    try:
        todoist_tasks = get_todoist_tasks()
        notion_tasks = get_notion_tasks()
        
        # Crear un diccionario para asociar el título de la tarea en Notion con el item completo (para poder comparar)
        notion_tasks_dict = {
            item["properties"]["Task Name"]["title"][0]["text"]["content"]: item
            for item in notion_tasks["results"] if item["properties"]["Task Name"].get("title")
        }
        
        # Tareas nuevas: las que no existen en Notion
        new_tasks = [task for task in todoist_tasks if task["content"] not in notion_tasks_dict]
        for task in new_tasks:
            result = add_task_to_notion(task)
            print(f"Tarea añadida a Notion: {result}")
        
        # Tareas existentes: se comparan y se actualizan solo si es necesario
        existing_tasks = [task for task in todoist_tasks if task["content"] in notion_tasks_dict]
        for task in existing_tasks:
            notion_item = notion_tasks_dict[task["content"]]
            if task_needs_update(task, notion_item):
                print(f"La tarea '{task['content']}' presenta cambios, se procede a la actualización...")
                page_id = notion_item["id"]
                result = update_task_in_notion(page_id, task)
                print(f"Tarea actualizada en Notion: {result}")
            else:
                print(f"La tarea '{task['content']}' no presenta cambios, se omite la actualización.")
        
        # Tareas en Notion que ya no están en Todoist: se archivarán (eliminan)
        todoist_titles = {task["content"] for task in todoist_tasks}
        for title, notion_item in notion_tasks_dict.items():
            if title not in todoist_titles:
                print(f"La tarea '{title}' ya no existe en Todoist, se procederá a archivar.")
                page_id = notion_item["id"]
                result = delete_task_in_notion(page_id)
                print(f"Tarea archivada en Notion: {result}")
                
    except requests.RequestException as e:
        print(f"Ocurrió un error: {e}")

if __name__ == "__main__":
    main()
