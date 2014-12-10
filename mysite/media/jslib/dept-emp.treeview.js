department=[];
function getDept_to_show_emp(lheight){
	$("#show_dept_emp_tree").html(getLayout_html(lheight));
	$.ajax({
	        type: "POST",
	        url:"/iclock/data/department/?l=10000&t=dept_json.js",
	        dataType:"json",
	        success:function(json){
	             department=json;
				ShowDept_Emp_Tree();
	        }
	});
}
function getLayout_html(lheight)
{
	var layout_html="<table width='100%' style='min-height: 160px;'><tr><td class='border_td'>"
						+"<div>"
								+"<div id='id_opt_tree'>"
						        +"<span>"+gettext("Department")+"</span><span style='float: right;margin-top:-18px;'>"
								+"<a href='#' id='id_expendAll'><img src='/media/img/images/expandAll.png' />&nbsp;&nbsp;"+gettext("Expand")+"</a>&nbsp;&nbsp;"
								+"<a href='#' id='id_collapseAll'><img src='/media/img/images/collapseAll.png' />&nbsp;&nbsp;"+gettext("Collaspe")+"</a>&nbsp;&nbsp;"
								+"<a href='#' id='id_refresh'><img src='/media/img/images/refresh.png' />&nbsp;&nbsp;"+gettext("Refresh")+"</a>"
								+"</span></div>"
						        +"<div id='showTree' style='overflow: auto;height:"+lheight+"px;width:250px;'></div>"
						+"</div></td>"
						+"<td class='border_td'><div>"
							+"<div><span class='title_bar'>"+gettext("Employee")+"</span></div>"
								+"<div style='overflow:auto;height:"+(lheight+25)+"px;width:400px;scrollWidth:600px;' id='id_emp'></div>"
						+"</div>"
						+"<input type='hidden' value='' id='hidden_depts' />"
						+"</td></tr></table>"
	return layout_html;

}
function click_dept()
{
	$("#deptBrowser a").click(function(event) {
		$.cookie("q","",{expires:0});
		var deptID=$(this).attr("alt");
		var result=getResult(deptID);  //得到父部门deptID第一级子部门
		arr_children=getDeptIDs(result);
		arr_children.push(deptID);     //父部门及其子部门信息
		$("#hidden_depts").val(arr_children);
		renderEmpTbl(1);
		event.preventDefault();
		event.stopPropagation();
		return true;
	});


}
function ShowDept_Emp_Tree()
{
	$("#showTree").html(getDeptTree(0,0));
	$("#deptBrowser").treeview();
//	$("#deptBrowser").css("width", "550px");
	$("#id_emp").html("<div align='center'><h4><img src='/media/img/icon_alert.gif'/>"+gettext("Click the department to show the employees!")+"</h4></div>");
	click_dept();
	$("#id_expendAll").click(function(){
		$("#showTree").html(getDeptTree(0,0));
		$("#deptBrowser").treeview();
		click_dept();
	});
	$("#id_collapseAll").click(function(){
		$("#showTree").html(getDeptTree(1,0));
		$("#deptBrowser").treeview();
		click_dept();
	});

	$("#id_refresh").click(function(){
		$("#showTree").html(getDeptTree(0,0));
		$("#deptBrowser").treeview();
		click_dept();
	});


}
function renderEmpTbl(p){
	if($.cookie("q")==null||$.cookie("q")=="")
		urlStr="/iclock/data/employee/?ot=0&t=empsInDept.html&DeptID__DeptID__in="+arr_children+"&p="+p;
	else
		urlStr="/iclock/data/employee/?ot=0&t=empsInDept.html&DeptID__DeptID__in="+arr_children+"&q="+$.cookie("q")+"&p="+p
	var text=$.ajax({
		url: urlStr,
		async: false
		}).responseText;
	$("#id_emp").html(text);

}

function getDeptTree(show,check){   //得到部门树
	var tree="<ul id='deptBrowser' class='filetree' style='margin-left:0px;'>";
	var parent=getResult(department[0].parent);//取得根部门
	if(parent.length>0)
		tree+=getTreeString(parent,show,check)+"</ul>";
	else
		tree+=getTreeString(department[0],show,check)+"</ul>"
	return tree;
}
function getTreeString(result,show,check) //递归生成树
{
	var tree_sub="";
	for(var i=0;i<result.length;i++)
	{
		if(show==1)
			var subStr="<li class='closed'>";
		else
		   var subStr="<li>";
		var children=getResult(result[i].DeptID);
		if(children.length>0){
			if(check==2)
				subStr+="<span class='folder'><input class='parent' alt1='"+result[i].parent+"' type='checkbox' alt='"+result[i].DeptID+"' />"+result[i].DeptName+"</span><ul>";
			else
				subStr+="<span class='folder'><a href='#' alt='"+result[i].DeptID+"'>"+result[i].DeptName+"</a></span><ul>";
			subStr+=getTreeString(children,show,check);
			subStr+="</ul>"
		}
		else{
			if(check==2)
				subStr+="<span class='file'><input alt1='"+result[i].parent+"' type='checkbox' alt='"+result[i].DeptID+"' />"+result[i].DeptName+"</span>";
			else
				subStr+="<span class='file'><a href='#'  alt='"+result[i].DeptID+"'>"+result[i].DeptName+"</a></span>";
		}
	tree_sub+=subStr+"</li>";
	}
	return tree_sub;
}

function getResult(parent){ //得到对应父部门的第一级子部门
	var children=[];
	for(var i=0;i<department.length;i++)
		if(parent==department[i].parent)
			children.push(department[i]);
	return children;
}
function getDeptIDs(result){ //得到对应父部门的所有子部门IDs
	var dept_children=[];
	for(var i=0;i<result.length;i++){
		var child=[];
		var children=getResult(result[i].DeptID);
		if(children.length>0)
			{
				child.push(result[i].DeptID)
				child.push(getDeptIDs(children));
			}
		else{
			child.push(result[i].DeptID);
			}
	dept_children.push(child);
	}

	return dept_children;
}
function showSelected_emp(){
    var c = 0;
    $.each($(".class_select_emp"),function(){
			if(this.checked) c+=1;})
    $("#selected_count").html("" + c);
}

function check_all_for_row_emp(checked) {

    if (checked) {
        $(".class_select_emp").attr("checked", "true");
    } else {
        $(".class_select_emp").removeAttr("checked");
    }
    showSelected_emp();
}
function getSelected_emp() {
	var emp=[];
	$.each($(".class_select_emp"),function(){
			if(this.checked)
				emp.push(this.id)
	});
	return emp;
}
function getSelected_empPin() {
	var pin=[];
	$.each($(".class_select_emp"),function(){
			if(this.checked) 
				pin.push(this.alt)
	});
	return pin;
}

function getSelected_empNames(){
	var empNames=[];
	$.each($(".class_select_emp"),function(){
			if(this.checked)
				empNames.push(this.name)
	});
	return empNames;
}

function getSelected_dept() {
	var dept=[];
	$.each($(".folder input"),function(){
			if(this.checked)
				dept.push(this.alt)
	});
	$.each($(".file input"),function(){
				if(this.checked)
					dept.push(this.alt)
		});
	return dept;
}
