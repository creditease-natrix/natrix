webpackJsonp([2],{"0VkS":function(e,s,t){"use strict";Object.defineProperty(s,"__esModule",{value:!0});var a={name:"",components:{},data:function(){return{user:"",pw:"",confirmPw:""}},mounted:function(){},methods:{register:function(){/^([a-zA-Z0-9]+[_|\_|\.]?)*[a-zA-Z0-9]+@([a-zA-Z0-9]+[_|\_|\.]?)*[a-zA-Z0-9]+\.[a-zA-Z]{2,3}$/.test(this.user)?/^[\w]{6,16}$/.test(this.pw)?this.pw===this.confirmPw?this.registerHandle():this.$message({type:"error",message:"您两次输入的密码不一致"}):this.$message({type:"error",message:"您输入的密码格式不正确，请重新输入"}):this.$message({type:"error",message:"您输入的邮箱格式不正确，请重新输入"})},registerHandle:function(){var e=this;this.$post({url:HP1+"/rbac/user/register/v1",data:{username:this.user,password:this.pw,verify_password:this.confirmPw}}).then(function(s){200==s.data.code?(e.$message({type:"success",message:"注册成功！"}),setTimeout(function(e){window.location.href=NatrixIndex},1e3)):e.$message({type:"error",message:s.data.message})})}}},o={render:function(){var e=this,s=e.$createElement,t=e._self._c||s;return t("div",{staticClass:"hold-transition login-page"},[t("div",{staticClass:"login-box"},[e._m(0),e._v(" "),t("div",{staticClass:"login-box-body"},[t("p",{staticClass:"login-box-msg"},[e._v("Natrix账号注册")]),e._v(" "),t("div",{staticClass:"form-group has-feedback"},[t("input",{directives:[{name:"model",rawName:"v-model",value:e.user,expression:"user"}],staticClass:"form-control",attrs:{name:"username",type:"text",placeholder:"电子邮箱"},domProps:{value:e.user},on:{input:function(s){s.target.composing||(e.user=s.target.value)}}}),e._v(" "),t("span",{staticClass:"glyphicon glyphicon-envelope form-control-feedback"})]),e._v(" "),t("div",{staticClass:"form-group has-feedback"},[t("input",{directives:[{name:"model",rawName:"v-model",value:e.pw,expression:"pw"}],staticClass:"form-control",attrs:{name:"password",type:"password",placeholder:"密码"},domProps:{value:e.pw},on:{input:function(s){s.target.composing||(e.pw=s.target.value)}}}),e._v(" "),t("span",{staticClass:"glyphicon glyphicon-lock form-control-feedback"})]),e._v(" "),t("div",{staticClass:"form-group has-feedback"},[t("input",{directives:[{name:"model",rawName:"v-model",value:e.confirmPw,expression:"confirmPw"}],staticClass:"form-control",attrs:{name:"password",type:"password",placeholder:"确认密码"},domProps:{value:e.confirmPw},on:{input:function(s){s.target.composing||(e.confirmPw=s.target.value)}}}),e._v(" "),t("span",{staticClass:"glyphicon glyphicon-lock form-control-feedback"})]),e._v(" "),t("div",{staticClass:"row"},[t("el-button",{attrs:{type:"info",size:"mini"},on:{click:e.register}},[e._v("立即注册")])],1)])])])},staticRenderFns:[function(){var e=this.$createElement,s=this._self._c||e;return s("div",{staticClass:"login-logo"},[s("a",{attrs:{href:""}},[s("b",[this._v("Natrix")])])])}]};var r=t("VU/8")(a,o,!1,function(e){t("TxS4"),t("RTCY")},"data-v-5c6834ca",null);s.default=r.exports},RTCY:function(e,s){},TxS4:function(e,s){}});