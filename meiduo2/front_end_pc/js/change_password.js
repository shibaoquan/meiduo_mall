var vm = new Vue({
    el: "#change_password",
    data: {
        host: host,
        user_id: '',
        password: '',
        password1: '',
        password2: '',


        // 控制表单显示
        is_show_form_1: true,
        is_show_form_2: false,
        is_show_form_3: false,
        is_show_form_4: false,

        error_password: false,
        error_check_password: false,

        // 控制进度条显示
        step_class: {
            'step-1': true,
            'step-2': false,
            'step-3': false,
            'step-4': false
        },

    },

    // 第三步
        check_pwd: function (){
            var len = this.password.length;
            if(len<8||len>20) {
                this.error_password = true;
            } else {
                this.error_password = false;
            }
        },
        check_cpwd: function (){
            if(this.password!=this.password2) {
                this.error_check_password = true;
            } else {
                this.error_check_password = false;
            }
        },
        on_submit: function(){
            this.check_pwd();
            this.check_cpwd();
            if (this.error_password == false && this.error_check_password == false) {
                axios.post(this.host + '/users/'+ this.user_id +'/password/', {
                        password: this.password,
                        password1: this.password1,
                        password2: this.password2,

                        // access_token: this.access_token
                    }, {
                        responseType: 'json'
                    })
                    .then(response => {
                        this.step_class['step-4'] = true;
                        this.step_class['step-3'] = false;
                        this.is_show_form_3 = false;
                        this.is_show_form_4 = true;
                    })
                    .catch(error => {
                        alert(error.response.data.message);
                        console.log(error.response.data);
                    })
            }
        }
});