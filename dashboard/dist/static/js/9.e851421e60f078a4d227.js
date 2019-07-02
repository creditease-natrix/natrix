webpackJsonp([9],{IOI2:function(t,e){},aBIn:function(t,e,a){"use strict";Object.defineProperty(e,"__esModule",{value:!0});var n=a("woOf"),i=a.n(n),r={name:"",components:{page:a("js5j").a},data:function(){return{href:ManageIndex,page_Count:1,pageShow:!1,tableData:[],searchWord:"",checkList:["无登记组织","组织信息不一致"],inactive:!1,unregister:!0,unmatch:!0,span_col_index:[0,1,2,6,7]}},created:function(){},watch:{checkList:function(t,e){-1!=t.indexOf("不活跃")?this.inactive=!0:this.inactive=!1,-1!=t.indexOf("无登记组织")?this.unregister=!0:this.unregister=!1,-1!=t.indexOf("组织信息不一致")?this.unmatch=!0:this.unmatch=!1,this.getTerminalCheckList(1)}},mounted:function(){this.getTerminalCheckList(1)},methods:{pageChangeHandle:function(t){this.getTerminalCheckList(t)},getTerminalCheckList:function(t){var e=this;this.$get({url:HP1+"/terminal/device/exceptions/v1",data:{inactive:this.inactive,unregister:this.unregister,unmatch:this.unmatch,search:this.searchWord,is_paginate:!0,pagenum:t}}).then(function(t){200==t.data.code&&(e.updateTableData(t.data.info),e.page_Count=t.data.page_count,e.pageShow=e.page_Count>0)})},handleEdit:function(t,e){this.$router.push({path:"editTerminal",query:{sn:e.sn}})},getTerminalDetail:function(t){this.$router.push({path:"terminalDetail",query:{sn:t}})},updateTableData:function(t){var e=this;this.tableData=[],t.forEach(function(t){var a={sn:t.sn,detect_orgs:t.detect_orgs,reg_orgs:t.reg_orgs,status:e.$t(t.status),terminal_local_ip:null,terminal_name:null,terminal_status:null,terminal_is_active:null},n=t.terminals;a.row_num=n.length>0?n.length:1,a.index=0,0==n.length?e.tableData.push(a):n.forEach(function(t,n){var r={};(r=i()(r,a)).index=n,r.terminal_local_ip=t.local_ip,r.terminal_name=t.name,r.terminal_status=e.$t(t.status),r.terminal_is_active=t.is_active,e.tableData.push(r)})})},tableSpan:function(t){var e=t.row,a=(t.column,t.rowIndex,t.columnIndex);if(-1!=this.span_col_index.indexOf(a))return 0==e.index?{rowspan:e.row_num,colspan:1}:{rowspan:0,colspan:0}}}},s={render:function(){var t=this,e=t.$createElement,a=t._self._c||e;return a("div",[a("div",{attrs:{id:"nav"}},[a("span",{staticClass:"title"},[t._v("终端管理——终端设备校验列表")]),t._v(" "),a("el-breadcrumb",{attrs:{"separator-class":"el-icon-arrow-right"}},[a("a",{staticClass:"home",attrs:{href:t.href}},[t._v(" 管理系统 "),a("i",{staticClass:"el-breadcrumb__separator el-icon-arrow-right"})]),t._v(" "),a("el-breadcrumb-item",{attrs:{to:{path:""}}},[t._v("终端管理")]),t._v(" "),a("el-breadcrumb-item",{attrs:{to:{path:"/terminalCheckList"}}},[t._v("终端设备校验")])],1)],1),t._v(" "),a("div",{staticClass:"optionBox clear"},[a("span",{staticClass:"listOption"},[a("el-checkbox-group",{model:{value:t.checkList,callback:function(e){t.checkList=e},expression:"checkList"}},[a("el-checkbox",{attrs:{label:"不活跃"}}),t._v(" "),a("el-checkbox",{attrs:{label:"无登记组织"}}),t._v(" "),a("el-checkbox",{attrs:{label:"组织信息不一致"}})],1)],1),t._v(" "),a("el-input",{staticStyle:{width:"300px",float:"right"},attrs:{id:"searchBtn",placeholder:"根据mac、ip、客户端版本和组织名称搜索",size:"mini"},nativeOn:{keyup:function(e){if(!("button"in e)&&t._k(e.keyCode,"enter",13,e.key,"Enter"))return null;t.getTerminalCheckList(1)}},model:{value:t.searchWord,callback:function(e){t.searchWord=e},expression:"searchWord"}},[a("el-button",{attrs:{slot:"append",icon:"el-icon-search",size:"mini"},on:{click:function(e){t.getTerminalCheckList(1)}},slot:"append"},[t._v("查询")])],1)],1),t._v(" "),a("el-table",{staticStyle:{width:"100%,margin-top:50px"},attrs:{data:t.tableData,"span-method":t.tableSpan,border:""}},[a("el-table-column",{attrs:{prop:"sn",label:"序列号",width:"170"},scopedSlots:t._u([{key:"default",fn:function(e){return[a("a",{staticClass:"nameLink",on:{click:function(a){t.getTerminalDetail(e.row.sn)}}},[t._v(t._s(e.row.sn))])]}}])}),t._v(" "),a("el-table-column",{attrs:{prop:"name",label:"登记职场"},scopedSlots:t._u([{key:"default",fn:function(e){return t._l(e.row.reg_orgs,function(e,n){return a("el-popover",{key:n,attrs:{trigger:"hover",placement:"top"}},[a("p",[t._v("名称: "+t._s(e.desc))]),t._v(" "),a("div",{staticClass:"name-wrapper",attrs:{slot:"reference"},slot:"reference"},[a("el-tag",{attrs:{size:"medium"}},[t._v(t._s(e.name))])],1)])})}}])}),t._v(" "),a("el-table-column",{attrs:{prop:"type",label:"检测职场"},scopedSlots:t._u([{key:"default",fn:function(e){return t._l(e.row.detect_orgs,function(e,n){return a("el-popover",{key:n,attrs:{trigger:"hover",placement:"top"}},[a("p",[t._v("名称: "+t._s(e.desc))]),t._v(" "),a("div",{staticClass:"name-wrapper",attrs:{slot:"reference"},slot:"reference"},[a("el-tag",{attrs:{size:"medium"}},[t._v(t._s(e.name))])],1)])})}}])}),t._v(" "),a("el-table-column",{attrs:{prop:"terminal_name",width:"120",label:"终端名称"}}),t._v(" "),a("el-table-column",{attrs:{prop:"terminal_local_ip",width:"120",label:"IP地址"}}),t._v(" "),a("el-table-column",{attrs:{prop:"terminal_status",width:"120",label:"终端状态"},scopedSlots:t._u([{key:"default",fn:function(e){return[a("span",{staticClass:"terminalStatus",class:{success:e.row.terminal_is_active,error:!e.row.terminal_is_active}},[t._v(t._s(e.row.terminal_status))])]}}])}),t._v(" "),a("el-table-column",{attrs:{prop:"status",width:"120",label:"状态"}}),t._v(" "),a("el-table-column",{attrs:{label:"操作"},scopedSlots:t._u([{key:"default",fn:function(e){return[a("el-button",{attrs:{size:"mini",type:"warning"},on:{click:function(a){t.handleEdit(e.$index,e.row)}}},[t._v("\n                    修改\n                ")])]}}])})],1),t._v(" "),a("page",{directives:[{name:"show",rawName:"v-show",value:t.pageShow,expression:"pageShow"}],attrs:{pageCount:t.page_Count},on:{"page-change":t.pageChangeHandle}})],1)},staticRenderFns:[]};var l=a("VU/8")(r,s,!1,function(t){a("IOI2"),a("it8+")},"data-v-251377b8",null);e.default=l.exports},"it8+":function(t,e){}});