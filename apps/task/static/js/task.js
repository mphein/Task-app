"use strict";

function clone(obj) { return JSON.parse(JSON.stringify(obj)); }

let app = {}
app.config = {
    data: function() {
        return {
            title: '',
            description: '',
            deadline: '',
            status: 'pending',
            users: [],
            searchQuery: '',
            assignedUser: '',
        };
    },
    methods: {
        createTask() {
            const taskData = {
                title: this.title,
                description: this.description,
                deadline: this.formatDeadline(this.deadline),
                status: this.status,
                assigned_to: this.assignedUser
            };
            console.log("Data being sent to API:", taskData);

            axios.post('/task/api/create_task', taskData).then(response => {
                console.log(response.data);
            }).catch(error => {
                // Handle the error here
                console.error(error);
            });
            this.clear()
        },
        clear() {
            this.title = '';
            this.description = '';
            this.deadline = '';
        },
        formatDeadline(datetimeLocal) {
            if (!datetimeLocal) return '';
            return datetimeLocal.replace('T', ' ');
        },
        copy() {
            const textToCopy = `Title: ${this.title}\nDescription: ${this.description}`;
            navigator.clipboard.writeText(textToCopy).then(() => {
                console.log('Text copied to clipboard');
            }).catch(err => {
                console.error('Failed to copy text: ', err);
            });
        },
        cancel() {
            window.history.back();
        },
        getUsers(query) {
            this.users = []
            console.log("getting users")
            fetch(`/task/api/search_users?query=${query}`).then(response => response.json())
                .then(data => {
                // Check if data is an array
                console.log(data.users);
                for (let i = 0; i < data.users.length; i++) {
                    // Push each user into the users array
                    this.users.push(data.users[i]);
                }
            }).catch(error => {
                 console.error('Error fetching users:', error);
            });
        },
        selectUser(user) {
            // Assign the selected user to the input field
            this.searchQuery = `${user.first_name.trim()} ${user.last_name.trim()}`;
            this.assignedUser = user.id;
        },
        editTask(task) {
            console.log("got here")
            this.cancelEdit();
            this.editing = {current: task, old: clone(task)};
        },
        cancelEdit() {
            if (this.editing.current)
                for(var key in this.editing.current)
                    this.editing.current[key] = this.editing.old[key];
            this.editing = {current: null};
        },
        saveTask(task) {
            const taskId = task.task.id;
            fetch(`/task/api/save_task/${taskId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(task)
            })
            .then(() => {
                this.editing = {current: null, old: {}};
            })
            .catch(error => console.error('errors:', error));
        },
        canEdit(task) {
            const assignedTo = task.assigned_to;
            const createdBy = `${task.auth_user.first_name} ${task.auth_user.last_name}`;
            return this.currentUser === assignedTo || this.currentManager === createdBy;
        }, 
        loadTasks() { 
            fetch('/task/api/get_tasks').then(response => response.json())
            .then(data => {
                this.tasks = data.tasks;
            })
            .catch(error => console.error('Error fetching tasks:', error));
        },
        getUrl(controller, id) {
            return `/${controller}/${id}`;
        },
    },
    watch: {
        searchQuery(newQuery) {
            console.log("searchQuery changed:", newQuery);
            this.getUsers(newQuery);
        }
    },
    mounted() {
        console.log("Vue instance mounted"); 
        this.getUsers('');   
        this.loadTasks();
    }
};

app.vue = Vue.createApp(app.config).mount("#app2");