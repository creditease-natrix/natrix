webpackJsonp([10],{kyzu:function(t,e,a){"use strict";Object.defineProperty(e,"__esModule",{value:!0});var n={name:"",components:{page:a("js5j").a},data:function(){return{href:ManageIndex,tableData:[],searchWord:"",statusTxt:"all",page_Count:1,pageShow:!1,options:[{value:"all",label:"全部"},{value:"active",label:"激活"},{value:"maintain",label:"维护"}],activeTxt:"all",activeOptions:[{value:"all",label:"全部"},{value:"yes",label:"是"},{value:"no",label:"否"}],currentPageNum:1}},created:function(){},watch:{$route:function(t,e){this.getMonitorSiteList(1)}},mounted:function(){this.getMonitorSiteList(1)},methods:{pageChangeHandle:function(t){this.currentPageNum=t,this.getMonitorSiteList(t)},getMonitorSiteList:function(t){var e=this,a={sn:this.$route.query.sn,search:this.searchWord,status:this.statusTxt,is_active:this.activeTxt,is_paginate:!0,pagenum:t};this.$post({url:HP1+"/terminal/terminal/list/v1",data:a}).then(function(t){200==t.data.code&&(e.tableData=t.data.info,e.tableData.forEach(function(t,a){t.statusTxt=e.$t(t.status),t.type=e.$t(t.type)}),e.page_Count=t.data.page_count,e.pageShow=t.data.page_count>0)})},getActiveOperation:function(t,e){var a=this;this.$put({url:HP1+"/terminal/terminal/operation/v1",data:{mac:e.macaddress,operation:"active"}}).then(function(t){200==t.data.code?a.getMonitorSiteList(a.currentPageNum):a.$message({type:"error",message:t.data.message})})},getMaintainOperation:function(t,e){var a=this;this.$put({url:HP1+"/terminal/terminal/operation/v1",data:{mac:e.macaddress,operation:"maintain"}}).then(function(t){200==t.data.code?a.getMonitorSiteList(a.currentPageNum):a.$message({type:"error",message:t.data.message})})},getDelOperation:function(t,e){var a=this;this.$confirm("此操作将永久删除该记录, 是否继续?","提示",{confirmButtonText:"确定",cancelButtonText:"取消",type:"warning"}).then(function(){a.delHandle(e)}).catch(function(){a.$message({type:"info",message:"已取消删除"})})},delHandle:function(t){var e=this;this.$put({url:HP1+"/terminal/terminal/operation/v1",data:{mac:t.macaddress,operation:"delete"}}).then(function(t){200==t.data.code?(e.$message({type:"success",message:"删除成功！"}),e.getMonitorSiteList(e.currentPageNum)):e.$message({type:"error",message:t.data.message})})}}},i={render:function(){var t=this,e=t.$createElement,a=t._self._c||e;return a("div",[a("div",{attrs:{id:"nav"}},[a("span",{staticClass:"title"},[t._v("终端管理——终端列表")]),t._v(" "),a("el-breadcrumb",{attrs:{"separator-class":"el-icon-arrow-right"}},[a("a",{staticClass:"home",attrs:{href:t.href}},[t._v("管理系统"),a("i",{staticClass:"el-breadcrumb__separator el-icon-arrow-right"})]),t._v(" "),a("el-breadcrumb-item",{attrs:{to:{path:""}}},[t._v("终端管理")]),t._v(" "),a("el-breadcrumb-item",{attrs:{to:{path:"/terminalList"}}},[t._v("终端设备列表")])],1)],1),t._v(" "),a("div",{staticClass:"optionBox clear"},[a("div",{staticClass:"fl"},[void 0!=this.$route.query.sn?a("span",[t._v("终端设备："+t._s(this.$route.query.sn))]):t._e()]),t._v(" "),a("div",{staticClass:"fr"},[a("span",[t._v("状态：")]),t._v(" "),a("el-select",{staticStyle:{display:"inline-block"},attrs:{size:"mini",placeholder:"请选择"},on:{change:function(e){t.getMonitorSiteList(1)}},model:{value:t.statusTxt,callback:function(e){t.statusTxt=e},expression:"statusTxt"}},t._l(t.options,function(t){return a("el-option",{key:t.value,attrs:{label:t.label,value:t.value}})})),t._v(" "),a("span",[t._v("活跃：")]),t._v(" "),a("el-select",{staticStyle:{display:"inline-block"},attrs:{size:"mini",placeholder:"请选择"},on:{change:function(e){t.getMonitorSiteList(1)}},model:{value:t.activeTxt,callback:function(e){t.activeTxt=e},expression:"activeTxt"}},t._l(t.activeOptions,function(t){return a("el-option",{key:t.value,attrs:{label:t.label,value:t.value}})})),t._v(" "),a("el-input",{staticStyle:{diaplay:"inline-block",width:"300px"},attrs:{id:"searchBtn",placeholder:"根据mac、ip、客户端版本和组织名称搜索",size:"mini"},nativeOn:{keyup:function(e){if(!("button"in e)&&t._k(e.keyCode,"enter",13,e.key,"Enter"))return null;t.getMonitorSiteList(1)}},model:{value:t.searchWord,callback:function(e){t.searchWord=e},expression:"searchWord"}},[a("el-button",{attrs:{slot:"append",icon:"el-icon-search",size:"mini"},on:{click:function(e){t.getMonitorSiteList(1)}},slot:"append"})],1)],1)]),t._v(" "),t._m(0),t._v(" "),a("el-table",{staticStyle:{width:"100%,margin-top:50px"},attrs:{data:t.tableData,border:""}},[a("el-table-column",{attrs:{prop:"macaddress",label:"mac",width:"150"},scopedSlots:t._u([{key:"default",fn:function(e){return[a("span",[t._v("\n                    "+t._s(e.row.macaddress)+"\n                    "),e.row.is_active?a("i",{staticClass:"icon iconfont icon-chongdian active"}):a("i",{staticClass:"icon iconfont icon-chongdian inActive"})])]}}])}),t._v(" "),a("el-table-column",{attrs:{prop:"name",label:"终端名称"}}),t._v(" "),a("el-table-column",{attrs:{prop:"type",width:"80",label:"类型"}}),t._v(" "),a("el-table-column",{attrs:{prop:"localip",width:"150",label:"IP地址"}}),t._v(" "),a("el-table-column",{attrs:{prop:"statusTxt",width:"120",label:"状态"}}),t._v(" "),a("el-table-column",{attrs:{prop:"children_num",width:"120",label:"能力"},scopedSlots:t._u([{key:"default",fn:function(e){return[a("span",{staticClass:"icon iconfont icon-wuxianjuyuwang",class:{success:e.row.access_intranet}}),t._v(" "),a("span",{staticClass:"icon iconfont icon-neiwang",class:{success:e.row.access_corporate}}),t._v(" "),a("span",{staticClass:"icon iconfont icon-gongsiwangdian",class:{success:e.row.access_internet}}),t._v(" "),a("span",{staticStyle:{"margin-left":"10px"}},[t._v(t._s(e.row.date))])]}}])}),t._v(" "),a("el-table-column",{attrs:{label:"操作"},scopedSlots:t._u([{key:"default",fn:function(e){return[a("el-button",{directives:[{name:"show",rawName:"v-show",value:"maintain"!=e.row.status,expression:"scope.row.status != 'maintain' "}],attrs:{size:"mini",type:"warning"},on:{click:function(a){t.getMaintainOperation(e.$index,e.row)}}},[t._v("\n                    维护\n                ")]),t._v(" "),a("el-button",{directives:[{name:"show",rawName:"v-show",value:"active"!=e.row.status,expression:"scope.row.status != 'active' "}],attrs:{size:"mini",type:"success"},on:{click:function(a){t.getActiveOperation(e.$index,e.row)}}},[t._v("\n                    激活\n                ")]),t._v(" "),a("el-button",{attrs:{size:"mini",type:"danger"},on:{click:function(a){t.getDelOperation(e.$index,e.row)}}},[t._v("\n                    删除\n                ")])]}}])})],1),t._v(" "),a("page",{directives:[{name:"show",rawName:"v-show",value:t.pageShow,expression:"pageShow"}],attrs:{pageCount:t.page_Count},on:{"page-change":t.pageChangeHandle}})],1)},staticRenderFns:[function(){var t=this.$createElement,e=this._self._c||t;return e("div",{staticClass:"statusTip"},[e("span",{staticClass:"listLabel"},[this._v("状态：")]),this._v(" "),e("span",{staticClass:"listOption"},[e("span",[e("i",{staticClass:"icon iconfont icon-wuxianjuyuwang"}),this._v("局域网访问")]),this._v(" "),e("span",[e("i",{staticClass:"icon iconfont icon-neiwang"}),this._v("企业网访问")]),this._v(" "),e("span",[e("i",{staticClass:"icon iconfont icon-gongsiwangdian"}),this._v("互联网访问")])])])}]};var s=a("VU/8")(n,i,!1,function(t){a("zLs3"),a("rRt4")},"data-v-08f53bc1",null);e.default=s.exports},rRt4:function(t,e){},zLs3:function(t,e){}});