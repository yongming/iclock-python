
delete dataExportsFormats[""];
if(typeof fieldHeaders=="object")
	options.tblHeader=fieldHeaders.join(" ")
function delAllRec()
{
	if(confirm(window.delAllHint?delAllHint(): gettext('Clear all data, are you sure?')))
		window.location.href="_clear_/"
}
function delOldRec(days)
{
	var ret=false;
	if(days==undefined || days==-1)
		ret=confirm(gettext('Delete out-of-date records, are you sure?'));
	else
		ret=confirm(gettext('Delete before _days_ days, out-of-date records, are you sure?').replace("_days_",days));
	if(ret) window.location.href="_del_old_/";
}

function setDataFilter(query, value)
{
	if( typeof(value)=="object")
	{
		var maxUrlLength=$.browser.msie?2000:(20*1024);
		while((value.join(",").length>maxUrlLength))
			value.pop(0);
	}
	loadPageData(query, value);
}

function showFilterChoices(s, name)
{
	var data=s.split("__")[0]
	if(data=="UserID")
		createDlgToUser(s,setDataFilter);
	else if(data=="DeptID")
		createDlgToDepartment(s,setDataFilter);
	else
		createDialog(s, setDataFilter, "miniData?key="+data, $.validator.format(gettext("Filter by {0}"),name), name, 350, true);
}
function createDlgToUser(url)
{

	var block_html="<div class='dialog' style='width:700px;min-height: 400px;'>"
					+ 		"<div class='dheader'>"+gettext('Select Employee')+"</div>"
					+ 		"<div class='dcontent'>"
					+           "<table width=100%>"
									+"<tr>"
									+"<td colspan='3' style='padding: 0;'><div id='show_dept_emp_tree' style='min-height: 200px;'></div></td>"
									+"<tr><td colspan='3'>"+createSubmitButton()+"</td></tr>"
									+"<tr><td colspan='3'>&nbsp;</td></tr>"
					+            "</table>"
					+       "</div>"


	$.blockUI(block_html);
    getDept_to_show_emp(350);
	blockUI_center();
    $("#btnShowOK").click(function(){
        emp=getSelected_emp();
        if( typeof(emp)=="object")
        {
            var maxUrlLength=$.browser.msie?2000:(20*1024);
            while((emp.join(",").length>maxUrlLength))
                emp.pop(0);
        }
		if(emp=="")
        	loadPageData(url);
		else
        	loadPageData(url, emp);
		$.unblockUI();
		$(".blockUI").hide();
    });
}
function createDlgToDepartment(url)
{

	var block_html="<div class='dialog' style='width:450px;'>"
					+ 		"<div class='dheader'>"+gettext("Select Department")+"</div>"
					+ 		"<div class='dcontent'>"
					+           "<table width=100%>"
									+"<tr>"
									+"<td colspan='3'>"
									+"<div>"
										+"<div id='id_opt_tree'>"
										+"<span>"+gettext("Department")+"</span>"
										+"<a href='#' id='id_expendAll'><img src='/media/img/images/expandAll.png' />&nbsp;&nbsp;"+gettext("Expand")+"</a>&nbsp;&nbsp;"
										+"<a href='#' id='id_collapseAll'><img src='/media/img/images/collapseAll.png' />&nbsp;&nbsp;"+gettext("Collaspe")+"</a>&nbsp;&nbsp;"
										+"<a href='#' id='id_refresh'><img src='/media/img/images/refresh.png' />&nbsp;&nbsp;"+gettext("Refresh")+"</a>&nbsp;&nbsp;"
										+"<input type='checkbox' id='id_contain_chl'/>&nbsp;&nbsp;"+gettext("Contain Children")
										+"</div>"
										+"<div id='showTree' style='overflow: auto;height:300px;'></div>"
									+"</div>"
									+"</td></tr>"
									+"<tr><td colspan='3'>"+createSubmitButton()+"</td></tr>"
									+"<tr><td colspan='3'>&nbsp;</td></tr>"
					+            "</table>"
					+       "</div>"

    
	$.blockUI(block_html);
	$("#showTree").html(getDeptTree(0,2));
   	$("#deptBrowser").treeview();
	$("#id_expendAll").click(function(){
   		$("#showTree").html(getDeptTree(0,2));
   		$("#deptBrowser").treeview();
		contain_child();

   	});
   	$("#id_collapseAll").click(function(){
   		$("#showTree").html(getDeptTree(1,2));
   		$("#deptBrowser").treeview();
		contain_child();

   	});

   	$("#id_refresh").click(function(){
   		$("#showTree").html(getDeptTree(0,2));
   		$("#deptBrowser").treeview();
		contain_child();
		
   	});
	contain_child();
	blockUI_center();
    $("#btnShowOK").click(function(){
        dept=getSelected_dept();
        if( typeof(dept)=="object")
        {
            var maxUrlLength=$.browser.msie?2000:(20*1024);
            while((dept.join(",").length>maxUrlLength))
                dept.pop(0);
        }
        loadPageData(url, dept);
		$.unblockUI();
    });
}
function contain_child()
{
$.each($("#id_contain_chl"),function(){	
		var ischecked=$.cookie("contain")
		if(ischecked==1)
			$(this).attr("checked","checked");
		else
			$(this).removeAttr("checked");
	});
	$("#id_contain_chl").click(function(){
		var ischecked=$(this).attr("checked");
		if(ischecked)
			ischecked=1;
		else
			ischecked=0;
		$.cookie("contain",ischecked, { expires: 7 });
	});
	$(".parent").click(function(){
		child=$(this).attr("alt");
		ischecked=$(this).attr("checked")
		if($("#id_contain_chl").attr("checked")){
			$.each($(".file input"),function(){
					if($(this).attr("alt1")==child ) 
						if(!ischecked)
							$(this).removeAttr("checked")
						else
							$(this).attr("checked","checked")
			});
			$.each($(".folder input"),function(){
				if($(this).attr("alt1")==child ){ 
					if(!ischecked)
						$(this).removeAttr("checked")
					else
						$(this).attr("checked","checked")
					child=$(this).attr("alt");
					ischecked=$(this).attr("checked")
					$.each($(".file input"),function(){
						if($(this).attr("alt1")==child ) 
							if(!ischecked)
								$(this).removeAttr("checked")
							else
								$(this).attr("checked","checked")
					});
				}
			});
		}
	});


}
function index_tip_info(obj)
{
	var index=$(obj).attr("index");
	$("#id_tip").html(getMoreInfo(index));
	var offset=$(obj).offset();
	if($("#id_tip").css("visibility")=="hidden"){
		$("#id_tip").css({"z-index":1024,"visibility":"visible","position":"absolute","top":(offset.top+30),"left":(offset.left+30)})
		$("#id_tip").mouseover(function(){
			$(this).css({"z-index":1024,"visibility":"visible","position":"absolute","top":(offset.top+30),"left":(offset.left+30)})
		
		}).mouseout(function(){
			$("#id_tip").css("visibility","hidden");
		});
	}
	else
		$("#id_tip").css("visibility","hidden");
	
}
function tip_info_exit()
{
	$("#id_tip").css("visibility","hidden")
}

function loadPageData(query, value)
{
	var postData={'addition_fields': options.addition_fields,'exception_fields': options.exception_fields};
	var url=pageQueryString;
	if(query!=undefined)
	{
		if(typeof query=="string")
		{
			if(value==undefined)
				url=getQueryStr(url, [query]);
			else if(value.length<1024)
				url=getQueryStr(url, [query], query+"="+value);
			else
			{
				url=getQueryStr(url,[query],"");
				postData[query]=value;
			}
		}
		else
		{
			if(value==undefined)
				url=getQueryStr(url, query);
			else if(typeof value=="object")
			{
				aurl="";
				for(var i in value) {
					if(i=='query') aurl=value[i];
					else postData[i]=value[i];
				}
				url=getQueryStr(url, query, aurl);
			}
			else
				url=getQueryStr(url, query,value);
		}
	}
	var postUrl=location.pathname+url;
    if(postUrl.indexOf("?")==-1){
		postUrl=postUrl+"?stamp="+new Date().getSeconds();
	}else{
        postUrl=postUrl+"&stamp="+new Date().getSeconds();
    }

	$.post(postUrl, 
		postData,
		function (d, textStatus) {
			if(d.errorCode==undefined)
			{
				var index=0;
				for(var f in d.field){
					var fname=d.field[f];
					d.field[fname]=index;
					if(d.header[index]=="")
					d.header[index]="<th>"+fname+"</th>";
					index++;
				}
				if(url.indexOf("action=")<0)
					pageQueryString=url;
				data=d;
				setShowStyle();
				$.unblockUI();
			}
			else
				alert(d.errorInfo)
		},
		"json");
}

function loadPage(pgNum)
{
	if(pgNum!=undefined) return loadPageData('p', pgNum);
	else return loadPageData();
}

$(function(){
if(!options.canAdd)$("#id_newrec").attr('disabled','true');
if(!options.canDelete) $("#id_clearrec").attr('disabled','true');
if(!options.canSearch) $("#changelist-search").remove();
if(!options.showStyle) $("#id_show_style").css('display','none');
if(dataExportsFormats.length>0) $("#id_export").show();
locations=location+"";
var searchStr=getKeyQuery("q");
if(searchStr!="")
{
	$("#searchbar").val(unescape(searchStr.substr(2)));
}

//搜索 
$("#changelist-search").submit(function(){
	var v=$("#searchbar")[0].value;
	if(v=="")
		loadPageData('q');
	else
		loadPageData('q',v);
	return false;
	});

//过滤 
$("#id_filterbar li ul li a").click(function(){
	if(this.protocol=="http:"){
		var newSearch=$(this).attr("href");
		var query=this.parentNode.parentNode.id.substr(4);
		if(newSearch.indexOf("?")>=0) newSearch=newSearch.split("?")[1];
		if(newSearch.indexOf("=")>0)
		{
			loadPageData([query+"__*"], newSearch);
		}
		else
		{
			loadPageData(query+"__*");
		}
		$("li", this.parentNode.parentNode).removeClass("selected");
		$(this.parentNode).addClass("selected");
		return false;
	}
	else
	{
		$("li", this.parentNode.parentNode).removeClass("selected");
		$(this.parentNode).addClass("selected");
		return true;
	}
});

var to=$.cookie("show"); 
$("input","#id_show_style").each(function(){
	if(to==$(this).val() && typeof(showBox)=='function')
		$(this).attr("checked","checked")
	if($.cookie("depart")=='tree' && to!=0)
		$(this).attr("checked","checked");
});

$("#id_loading").bind("ajaxSend", function(){
	  $(this).show();
	}).bind("ajaxComplete", function(){
		$(this).hide();
	});

//$().ajaxSend(function(){ $.blockUI();})
//$().ajaxComplete(function(){ $.unblockUI();})

loadPage();

$("input","#id_show_style").click(setShowStyle);

});

function setShowStyle(){
	var to=$.cookie("show");
	if($(this).attr("alt")=='tree'){
		$.cookie("depart", $(this).attr('alt'), { expires: 7 });
		$.cookie("show", $(this).val(), { expires: 7 });
	}
	else if($(this).attr("checked") && $(this).val()!=to){
		$.cookie("show", $(this).val(), { expires: 7 });
	}
	if($.cookie("show")==1 && typeof(showBox)=='function')
	{
		$("#id_showTbl").parent().find("#id_showTbl").html('<td colspan="2"><div id="iclockBox" class="box">'+showBox(data.data)+'</div></td>');
		renderTbl(data, options);
		$("#id_select_div").before('<div><input type="checkbox" class="class_select_all" onclick="check_all_for_row(this.checked);" />'+gettext("Select All")+'</div>')
	}
	else if($.cookie("depart")=='tree' && $.cookie("show")==1)
	{
		$("#id_searchbar").css("display","none");
		$("#id_showTbl").parent().find("#id_showTbl").html('<td colspan="2"><div id="show_dept_emp_tree"></div></td>')
		getDept_to_show_emp(400);
	}
	else
	{	
		$("#id_showTbl").parent().find("#id_showTbl").html('<td colspan=2 style="padding: 0px;"><table id="tbl" width="100%" border="1" ></table></div>')
		renderTbl(data, options);
	}
	
}

function exportData(url, value)
{
	url=getQueryStr(pageQueryString, [url], url+'='+value);
	window.location.href=location.pathname+url;
}

function exportRec()
{
	createDialog('f', exportData, dataExportsFormats, gettext("Export")+options.title+gettext("list"), gettext("format"), 350);
}


