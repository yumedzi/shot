from locust import HttpLocust, TaskSet, task

class WebsiteTasks(TaskSet):
    @task
    def debug(self):
        self.client.get("/debug")

class WebsiteUser(HttpLocust):
    task_set = WebsiteTasks
    # min_wait = 5000
    # max_wait = 15000
