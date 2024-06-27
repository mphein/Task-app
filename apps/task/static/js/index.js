let app = {}
function clone(obj) { return JSON.parse(JSON.stringify(obj)); }
app.config = {
    data: function(){
        return {
          filters: {
            created_by_self: false,
            assigned_to_self: false,
            created_by_user: '',
            assigned_to_user: '',
            created_by_managed: '',
            assigned_to_managed: '',
            sortOption: 'newestCreate',
            statusOption: 'all'
          },
            currentUser: '',
            currentManager: '',
            assignedUser: '',
            editing: {current: null, old: {}},
            statusOptions: ['pending', 'acknowledged', 'rejected', 'completed', 'failed'],
            users: [],
            tasks: [],
            newComment: '',
            comments: []
        };
      },
      methods: {
        clearFilter(){
          this.filters = {
            created_by_self: false,
            assigned_to_self: false,
            created_by_user: '',
            assigned_to_user: '',
          };
          this.loadTasks();
        },
        updateFilter(filter_name, id){
  
        },
        filterTask(){
            const filterData = {
                created_by_self: this.filters.created_by_self,
                assigned_to_self: this.filters.assigned_to_self,
                created_by_user: this.filters.created_by_user,
                assigned_to_user: this.filters.assigned_to_user,
                created_by_managed: this.filters.created_by_managed,
                assigned_to_managed: this.filters.assigned_to_managed
            };

            let queryString = `?created_by_self=${filterData.created_by_self}&assigned_to_self=${filterData.assigned_to_self}&created_by_user=${filterData.created_by_user}&assigned_to_user=${filterData.assigned_to_user}`;
            fetch(`/task/api/filter_task${queryString}`)
            .then(response => response.json())
            .then(data => {
                this.tasks = data.tasks;
                console.log(this.tasks)
                this.sortTasks();
            }).catch(error => {
                console.error('Error fetching tasks:', error)
           });
        },
        loadCurrentUser() {
          fetch('/task/api/get_current_user')
              .then(response => response.json())
              .then(data => {
                  this.currentUser = data.user;
                  if (data.manager) { this.currentManager = data.manager.id; }
                  console.log(this.currentUser);
                  console.log(this.currentManager);
              })
              .catch(error => console.error('Error fetching current user:', error));
        },
        getUsers(query) {
          this.users = [];
          console.log("getting users");
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
        loadTasks() { 
            fetch('/task/api/get_tasks').then(response => response.json())
            .then(data => {
                this.tasks = data.tasks;
                console.log(this.tasks);
                this.sortTasks();
                this.tasks.forEach(task => {
                  this.getComments(task.task.id);
                });
            })
            .catch(error => console.error('Error fetching tasks:', error));
        },
        editTask(task) {
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
            const assignedTo = task.task.assigned_to;
            const createdBy = `${task.auth_user.first_name} ${task.auth_user.last_name}`;
            console.log("assignedTo:", assignedTo);
            console.log("createdBy:", createdBy);
            console.log("currentUser:", this.currentUser);
            console.log("currentManager:", this.currentManager);
            return this.currentUser == assignedTo || this.currentManager == createdBy;
        }, 
        addComment(taskId) {
          const commentData = {
              task_id: taskId,
              body: this.newComment
          };
          axios.post('/task/api/add_comment', commentData).then(response => {
              console.log(response.data);
              this.newComment = '';
          }).catch(error => {
              console.error('Error adding comment:', error);
          });
        },
        getComments(taskId) {
          fetch(`/task/api/get_comments/${taskId}`)
            .then(response => response.json())
            .then(data => {
                this.comments = data.comments;
                console.log(this.comments);
            }).catch(error => {
                console.error('Error fetching comments:', error);
            });
        },
        sortTasks() {
          // Sort tasks by date created or deadline
          if (this.filters.sortOption === 'newestCreate') {
            console.log(this.filters.sortOption)
            this.tasks.sort((a, b) => new Date(b.task.created_on) - new Date(a.task.created_on));
          } else if (this.filters.sortOption === 'oldestCreate') {
            this.tasks.sort((a, b) => new Date(a.task.created_on) - new Date(b.task.created_on));
          } else if (this.filters.sortOption === 'upcomingDeadline') {
            this.tasks.sort((a, b) => new Date(a.task.deadline) - new Date(b.task.deadline));
          } else if (this.filters.sortOption === 'latestDeadline') {
            console.log("latest")
            this.tasks.sort((a, b) => new Date(b.task.deadline) - new Date(a.task.deadline));
          } 

          if (this.filters.statusOption !== 'all') {
            this.tasks = this.tasks.filter(task => task.task.status === this.filters.statusOption);
          }
        },
    },
    mounted() {  
        console.log("Vue instance mounted"); 
        this.getUsers('');   
        this.loadTasks();
        this.loadCurrentUser();
    }
  };
  app.vue = Vue.createApp(app.config).mount("#app1");