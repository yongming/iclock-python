$.blockUI.defaults.pageMessage="<img src='/media/img/loading.gif' />";
function actionSuccess(retdata)
{

	if(retdata.indexOf("result=0")==0)
		window.location.reload();
	else
	{
		var i=retdata.indexOf("errorInfo=\"");
		alert(retdata.substr(i+11,retdata.length-i-13));
		window.location.reload();
		//$.unblockUI()
	}
}
function actionSucess_NoReload(retdata)
{
	if(retdata.indexOf("result=0")==0){
		$.unblockUI();
	}
	else
	{
		var i=retdata.indexOf("errorInfo=\"");
		alert(retdata.substr(i+11,retdata.length-i-13));
	}

}
function createDialog(url, actionUrl, miniDataUrl, title, label, width, multiSel)
{
	//miniDataUrl:	for fill the select box
	//title:		dialog title
	//label:		select box title
	//width:		dialog width
	$.blockUI(miniDialog(title, label, width, multiSel));
	if(procMiniData(miniDataUrl))
		procSubmit("btnShowOK", url, actionUrl)
}

function procSubmit(btnID, url, actionUrl)
{
	if(typeof actionUrl=="function")
		$("#"+btnID).click(function() {actionUrl(url, $("#md_slt").val()); $.unblockUI();});
	else
		$("#"+btnID).click(function() {
			var slt = $("#md_slt").val();
			if (slt != "")
			{
				a = actionUrl + slt
				if(a.indexOf("action=")>=0 && url.ret.indexOf("K=")>=0)
				{
					$.blockUI();
					$.ajax({type: "POST",
						url: getQueryStr(window.location.href, ["action"], a),
						data: url.ret,
						dataType:"text",
						success: actionSuccess,
						error: function(request, errorMsg){
							alert(String.format(gettext('Operating failed for {0} : {1}'), options.title, errorMsg)); $.unblockUI();
							}
						});
				}
				else
					window.location.href = a +"&p="+page_index+url.ret
			}
		});
}

function procMiniData(miniDataUrl)
{
	$("#id_selvalue").keyup(function(){
			slt=$("#md_slt");
			text=$("#id_selvalue").val()
			if(text && slt)
			for(var i=0; i<slt[0].options.length; i++)
			{
				var opts=slt[0].options[i];
				if(opts)
				if( //(opts.value.indexOf((" "+text).substr(1,1000))>=0) ||
					(opts.text.indexOf(text)>=0))
				{
					slt[0].selectedIndex=opts.index;
					return;
				}
			}
		}
		);
	var cf=function(data){
			var htmlSlt = ""
			var c=0;
			for (var row in data)
			{
				htmlSlt += "<option value='" + row + "'>" +data[row] + "</option>";
				c++;
			}
			$("#md_slt").html(htmlSlt);
			if(c>10)
			{
				$("#id_selvalue").show();
				$("#id_selvalue").focus();
			}
			else
				$("#md_slt").attr('size', c<5?6: c);
			blockUI_center();
	}
	if(typeof miniDataUrl=="string")
		$.ajax({type: "GET", url: miniDataUrl, dataType:"json",
		success: function(data){
			if (data=="")
			{
				alert(String.format(gettext('No Data {0}'),label));
				$.unblockUI();
				return false
			}
			for (var row in data) data[row]= row+" ("+data[row]+")"
			cf(data);
		},
		error: function(ereq, text, errorThrown){
      alert('error ajax: "'+text+'"\n'+errorThrown);
      $.unblockUI();
      }
		});
	else
		cf(miniDataUrl);
	blockUI_center();
	return true;
}

function miniDialog(title, label, width, multiSel)
{
	return	"<div class='dialog' style='width:" + width + "px;'>"
		+ 		"<div class='dheader'>" + title + "</div>"
		+ 		"<div class='dcontent'>"
		+ 			"<input class='dtitle' value='"+String.format(gettext('Please Select {0}: '),label)+"' disabled style='color: #000 !important;' />"
		+	createMiniSel(multiSel, label)
		+	createSubmitButton()
		+   "<br/>"
		+ 	"</div>"
		+ 	"</div>"
}

function createMiniSel(multiSel)
{
	return "<div style='text-align:center; padding:0px;'>"
		+   "<input id='id_selvalue' type='text' style='display:none; width: 263px;' />"
		+ 	"<select size=12 id='md_slt' "+(multiSel?"multiple":"")+" style='width: 270px;'>"
		+ 	"<option>"+gettext('Loading data ...') + "</option>"
		+ 	"</select>"
		+	"</div>"
}

function createDateRangeDlg(header)
{
	var html=
		  "<div class='dialog'>"
		+  "<div class='dheader'>" + header + "</div>"
		+  "<div class='dcontent'>"
		+ 	"<input class='dtitle' value='"+gettext('Input the range of time:')+"' readonly />"
		+   createTimeRangeEdit() + createSubmitButton()
		+	"<br/>"
		+ "</div>"
		+"</div>"
	scroll(0,0);
	$.blockUI(html);
	blockUI_center();
	DateTimeShortcuts.init();
	$("div.clockbox").css("z-index",2005);
	$("div.calendarbox").css("z-index",2005);
	$("#btnShowCancel").click(function() {
			$("div.clockbox").hide();
			$("div.calendarbox").hide();
			$.unblockUI();
			});
	$("input.dtitle").focus(function(){
			$("#id_date_range_from")[0].focus();
			})
}

function createEndDateDlg(header)
{
	var html=
		  "<div class='dialog'>"
		+  "<div class='dheader'>" + header + "</div>"
		+  "<div class='dcontent'>"
		+ 	"<fieldset><legend class='dtitle'>"+gettext('AC Clock-in/out Records')+"</legend>"
		+   createDateEdit(0) 
		+	"</fieldset><br/>"
		+ 	"<fieldset><legend class='dtitle'>"+gettext('Attendance Checking Exception Records')+"</legend>"
		+   createDateEdit(1) 
		+	"</fieldset><br/>"
		+ 	"<fieldset><legend class='dtitle'>"+gettext('Shift Data for AC Time')+"</legend>"
		+   createDateEdit(2) 
		+	"</fieldset><br/>"
		+ createSubmitButton()
		+ "</div>"
		+"</div>"
	scroll(0,0);
	$.blockUI(html);
	blockUI_center();
	DateTimeShortcuts.init();
	$("div.clockbox").css("z-index",2005);
	$("div.calendarbox").css("z-index",2005);
	$("#btnShowCancel").click(function() {
			$("div.clockbox").hide();
			$("div.calendarbox").hide();
			$.unblockUI();
	});


}
function getDateRangeFor(fieldName)
{
	createDateRangeDlg(gettext('Please Input'));
	$("#btnShowOK").click(function() {
			var fromTime=$("#id_date_range_from").val();
			var toTime=$("#id_date_range_to").val();
			var url="";
			if(fromTime=="" ||toTime=="")
				url="";
			else
				url=(valiDateTimes(fromTime)?("&"+fieldName+"__gte="+fromTime):"")+(valiDateTimes(toTime)?("&"+fieldName+"__lte="+toTime):"");
			if(url=="") url=fieldName+"__isnull=True"
			window.location.href=getQueryStr(window.location.href, [fieldName+"*"], url)});
	$("#id_date_range_from")[0].focus();
}

function getCurFrontUrl()
{
	var scripts = document.getElementsByTagName('script');
	for (var i=0; i<scripts.length; i++) {
		if (scripts[i].src.match(/tools/)) {
			var idx = scripts[i].src.indexOf('jslib/tools');
			return scripts[i].src.substring(0, idx);
		}
	}
}

function blockUI_center()
{
	var box=$(".blockMsg")
	width = box.width()
	height = box.height()
	box.css('margin-left', (width/-2) + 'px')
	if(!($.browser.msie && $.browser.version<7.0)) box.css('margin-top', (height/-2*1) + 'px')
}

function getQueryStr(q, keys, append)
{
	if(append && append.indexOf('?')==0)
		append=append.substr(1,1000)
	if(q.indexOf('?')<0)
	{
		if(append) return "?"+append;
		return q;
	}
	var qry=q.split("?")[1].split("&");
	var newQry=[];
	var rm=0;
	for(var i in qry)
	{
		rm=0;
		qk=qry[i].split("=")[0];
		for(var j in keys)
		{
			var k=keys[j];
			if((k==qk) ||
				(k.substr(k.length-1,1)=="*" && qk.indexOf(k.substr(0,k.length-1))==0))
			{
				rm=1;
				break;
			}
		}
		if(0==rm && qry[i].length>0) newQry.push(qry[i]);
		//k.indexOf("&"+qk+"&")<0) newQry.push(qry[i]);
	}
	if(newQry.length)
		return "?"+newQry.join("&")+(append?("&"+append):"");
	else
		return append?("?"+append):q.split("?")[0];
}

function getKeyQuery(key)
{
	var q=window.location.href;
	if(q.indexOf('?')<0) return "";
	var qry=q.split("?")[1].split("&");
	for(var i in qry)
		if(qry[i].split("=")[0]==key) return qry[i];
	return "";
}

function repUrlKey(key, newValue)
{
	return getQueryStr(window.location.href, [key], newValue?key+'='+newValue:"");
}

function renderResultTbl(p,page_style) 
{

	var dept="&deptIDs="+$.cookie("deptIDs")
	if(page_style==2)
		urlStr="/iclock/data/attRecAbnormite/?o=checktime&ot=0&t=attRecAbnormite.html&UserID__id__in="+emp+"&checktime__gte="+ComeTime+"&checktime__lt="+EndDate+dept;
	if(page_style==3)
		urlStr="/iclock/data/attShifts/?o=AttDate&ot=0&t=attShifts.html&UserID__id__in="+emp+"&AttDate__gte="+ComeTime+"&AttDate__lt="+EndDate+dept;
	if(page_style==4)
		urlStr="/iclock/data/AttException/?ot=0&t=AttException.html&UserID__id__in="+emp+"&AttDate__gte="+ComeTime+"&AttDate__lt="+EndDate+dept;
	urlStr+="&p="+p;
	var text=$.ajax({
			url: urlStr,
			async: false
			}).responseText;
		$("#id_result").html(text);
		$("#tbl").flexigrid({});
		
}
function renderTransTbl(p)
{
	var text=$.ajax({
		url: "/iclock/data/transaction/?ot=0&t=empOfTrans.html&UserID__id__in="+emp+"&TTime__gte="+ComeTime+"&TTime__lte="+EndDate+"&p="+p,
		async: false
		}).responseText;
	$("#show_tranctions").html(text);



}
function pageUrl(pgNum,page_style) {
	if(typeof(page_style)=='undefined')
		return "<a href='"+getQueryStr(window.location.href, ["p"], "p="+pgNum)+"'>"+pgNum+"</a> ";
	else if(page_style==0)
		return "<a href='#' onclick='renderTransTbl("+pgNum+");'>"+pgNum+"</a> ";
	else if(page_style==1)
		return "<a href='#' onclick='renderEmpTbl("+pgNum+");'>"+pgNum+"</a> ";
	else 
		return "<a href='#' onclick='renderResultTbl("+pgNum+","+page_style+");'>"+pgNum+"</a> ";
	
}

function gotoPage(e,page_style)
{
	var keynum;
	var keychar;
	var numcheck;
	if(window.event) // IE
	{
		keynum = e.keyCode;
	}
	else if(e.which) // Netscape/Firefox/Opera
	{
		keynum = e.which;
	}
	if(13!=keynum) return true;
	pnum=parseInt($('#id_pageNumInput').val());
	if(isNaN(pnum)) pnum=1;
	if(typeof(page_style)=='undefined')
		window.location.href=getQueryStr(window.location.href, ["p"], "p="+pnum);
	else if(page_style==0)
		renderTransTbl(pnum);
	else if(page_style==1)
		renderEmpTbl(pnum);
	else
		renderResultTbl(pnum,page_style);
	
	return false;
}

function getPagers(title, startRecord, totalRecords, pageSize, currPg, totPg,page_style) {
  
    var last = startRecord + pageSize;
    if (last > totalRecords) {
        last = totalRecords;
    }
	
	if(title!="")
		title+=":"
		
	var s=(startRecord + 1) + "-" + last + String.format(gettext('(total {0})'),totalRecords)+ "&nbsp;&nbsp;";

	if (totPg<=1)
	{
		if(totalRecords>0)
			return String.format(gettext('total {0}'),totalRecords)
		else
			return gettext('None')
	}
	
	
	pf=gettext('Page:')+" <input id=id_pageNumInput value="+currPg+" type='text' onkeypress='return gotoPage(event,"+page_style+")' style='width: 35px !important;'> "
    if (currPg < 5) {
        s += pf;
        for (i = 1; i <= totPg && i <= currPg + 1; i++) {
            if (i == currPg) {
                s += "<font color=red>" + i + "</font> ";
            } else {
                s += pageUrl(i,page_style);
            }
        }
    } else {
        s += pf + pageUrl(1,page_style) + "... " + pageUrl((currPg - 1),page_style) + " <font color=red>" + currPg + "</font> " + (currPg == totPg ? "" : pageUrl((currPg + 1),page_style));
    }
    if (totPg - 3 <= currPg) {
        for (i = currPg + 2; i <= totPg; i++) {
            s += pageUrl(i,page_style);
        }
    } else {
        s += "... " + pageUrl(totPg,page_style);
    }
    return s;
}
function removeNone(s){return s=="None"?"":s}
function renderTbl(data, options)
{	
	var disableCol="";
	if(options.disableCols) disableCol=","+options.disableCols.toString()+",";
	for(var row in data)
	if(typeof sortData=="function") data.sort(sortData);
	var pagers=''
	var tpage='';
	var tpage2='';
	var item_count=0;
	var sel=getSelected(data, options.keyFieldIndex);
	for(var i in data)
	if((typeof filterData!="function") || filterData(data[i]))
	{
		var colI=0;
		var key=data[i][options.keyFieldIndex];
		var apage='';
		if(options.canSelectRow)
			apage+="<tr class=row"+(i%2+1)+" onclick='SelectRow(this);'>"+
				(options.showSelect?"<td class='class_select_col'><input type='checkbox' class='class_select' onclick='showSelected();' id='id_row_"+i+"' "+((sel.ret+"&").indexOf('&K='+key+'&')>=0?"checked":"")+"/></td>":"");
		else
			apage+="<tr class=row"+(i%2+1)+">"+
				(options.showSelect?"<td class='class_select_col'><input type='checkbox' class='class_select' onclick='showSelected();' id='id_row_"+i+"' "+((sel.ret+"&").indexOf('&K='+key+'&')>=0?"checked":"")+"/></td>":"");
		for(j in data[i])
			if(-1==disableCol.indexOf(","+j+","))
			{
				colI+=1;
				var colData=data[i][j];
				if(typeof colData=="function")
					colData=colData(data[i]);
				else
					colData=removeNone(colData);
				if(options.canEdit && colI==1) //window.document.location.pathname
					apage+="<td><a class='can_edit' href='"+key+"/'>"+colData+"</td>";
				else
					apage+="<td>"+colData+"</td>";
			}
		apage+="</tr>";
		tpage+=apage;
		if(item_count%20==0)
		{
			tpage2+=tpage;
			tpage='';
			if(item_count%100==0)
			{
				pagers+=tpage2;
				tpage2='';
			}
		}
		item_count+=1;
	}
	pagers+=(tpage2+tpage);
	$("#"+options.pagerId).html(getPagers(options.title, item_from-1, totalRecCnt, page_limit, page_index, page_number));

	$("#"+options.tblId).html("<thead><tr>"+(options.showSelect?"<th width='15px' class='class_select_col'><input type='checkbox' class='class_select_all' onclick='check_all_for_row(this.checked);' /> </th>":"")+options.tblHeader+"</tr></head><tbody>"+pagers+'</tbody>');
	if(options.showSelect && item_count>0)
	{
		html='<div id="id_select_div">&nbsp;&nbsp;&nbsp;'+gettext('Selected:')+' <span id="id_selected_count">0</span></div>';
		$(".selectedDataOp #id_defSelectDataOp").html(html+'<div>&nbsp;&nbsp;&nbsp;</div>');
		html=(options.canDelete?'<li><a id="aDelete" href="javascript: batchOp(\'?action=del\',true,\''+gettext('Delete')+'\');">'+gettext('Delete')+'</a></li>':
		                        '<li><div>'+gettext('Delete')+'</div></li>');
		if(typeof extraBatchOp=="object")
		{
			for(var i in extraBatchOp)
			{
				if(extraBatchOp[i].action)
					html+="<li><a href='javascript: batchOp("+i+")'>"+extraBatchOp[i].title+"</a></li>";
				else
					html+="<li><div>"+extraBatchOp[i].title+"</div></li>";
			}
		}
		if(html=='')
		  $("#op_menu_div").hide();
		else
		{
			$("#op_menu").html(html);
			$("#op_menu_div").css("display","inline");
		}
	}
	else
		$("#id_defSelectDataOp").html("");
	if (window.hide_batchOp) hide_batchOp();
	if (window.last_action) last_action();
	$("#"+options.tblId).flexigrid({});
}

function SelectRow(obj) {	
	if(typeof(PageSelectRow)=='function') PageSelectRow(data[obj.rowIndex]);
}

function showSelected() {
    var c = 0;
    $.each($(".class_select"),function(){
			var tr=this.parentNode.parentNode;
			if(tr.nodeName=="TD") tr=tr.parentNode;
			if(this.checked) {
				$(tr).addClass("trSelected");
				c+=1;
			}
			else
				$(tr).removeClass("trSelected");
			})
    $("#id_selected_count").html("" + c);
}

function check_all_for_row(checked) {
    if (checked) {
        $(".class_select").attr("checked", "true");
    } else {
        $(".class_select").removeAttr("checked");
    }
    showSelected();
}

function getSelected(data, keyIndex,itemCanSelect) {
	var ret="";
	var c=0, selCount=0;
	var ss=[];
	for(i=0; i<data.length; i++)
	{
		var obj=$("#id_row_"+i);
		if(obj.length>0 && obj[0].checked)
		{
			selCount++;
			if(typeof itemCanSelect!="function" || itemCanSelect(data[i]))
			{
				c++;
				ret+="&K="+data[i][keyIndex];
				if(typeof strOfData=="function")
					ss.push(strOfData(data[i]))
				else
					ss.push(data[i][keyIndex]);
			}
		}
	}
	var result={count: c, selectedCount: selCount, ret: ret, ss: ss};
	return result;
}

function formatArray(a)
{
	if(a.length<11) return a.join("\n");
	var ret='';
	var c=0;
	var aa=[];
	for(var i in a)
	{
		c++;
		if(c>10) break;
		aa.push(a[i]);
	}
	return aa.join("\n")+"\n... ...";
}

function batchOp(action, itemCanSelect, opName)
{
	if(typeof action=="number")
	{
		if(!itemCanSelect) itemCanSelect=extraBatchOp[action].itemCanBeOperated;
		if(!opName) opName=extraBatchOp[action].title;
		action=extraBatchOp[action].action;
	}
	else
		if(!opName) opName=gettext('Operation')
	var url=getSelected(data, options.keyFieldIndex, itemCanSelect);
	if(url.selectedCount==0)
		alert(String.format(gettext('Please Select {1} to {0}'),opName,options.title))
	else if(url.count==0)
		alert(String.format(gettext('{1} disallowed for {0}!'),options.title,opName))
	else
	{
		var a='';
		if(typeof action=="function")
			a=action(url);
		else if(window.confirm(String.format(gettext('Will {2} the {0} {1} ?'),url.count,options.title,opName)+
					(typeof ActionHint=="function"?ActionHint(action,opName):"")+
					"\n\n"+formatArray(url.ss)+"\n\n"+gettext('Please Confirm!')))
			a=action

		if(a)
		{
			//alert("a="+a+"\n\nret="+url.ret);
			//window.location.href=getQueryStr(window.location.href, ["action"],a+url.ret);
			$.blockUI()
			$.ajax({type: "POST",
					url: getQueryStr(window.location.href, ["action"],a),
					data: url.ret,
					dataType:"text",
					success: actionSuccess,
					error: function(request){
						alert(String.format(gettext('{0} failed!\n\n{1}'), opName, request.statusText)); $.unblockUI();
						$('body').html(request.responseText);
						}
					});
		}
	}
}

function searchKey(keyData)
{
	for(var i in data)
		if(keyData==data[i][options.keyFieldIndex]) return i;
	return -1;
}

function $s(s, len)
{
	if(!len) len=100
	if(s.length>len) return s.substr(0,len)+' ...';
	return s;
}

function createSubmitButton()
{
	str = "<div style='text-align:right; margin-top: 10px; margin-right: 20px;'>"
	str += '<input type="button" value="'+gettext('Submit')+'" id="btnShowOK" >&nbsp;&nbsp;&nbsp;'
	str += '<input type="button" value="'+gettext('Cancel')+'" id="btnShowCancel" onclick="$.unblockUI();">&nbsp;&nbsp;&nbsp;'
	str += "</div>"
	return str
}

function createTimeRangeEdit()
{
	return "<table style='text-align: center;'>"
		+  "<tr><td class='label'>"+gettext('Start Time:')+"</td><td><input id='id_date_range_from' width=19 class='vDateField' /></td></tr>"
		+  "<tr><td class='label'>"+gettext('End Time:')+"</td><td><input id='id_date_range_to' width=19 class='vDateField' /></td></tr>"
		+  "</table><div>&nbsp;</div><hr />"
}
function createDateEdit(index)
{
	return "<table style='text-align: center;'>"
		+  "<tr><td class='label'>"+gettext('End Time:')+"</td><td><input id='id_endTime"+index+"' width=19 class='vDateOnlyField' /></td></tr>"
		+  "</table><div>&nbsp;</div><hr />"
}

function createCheckBoxHtml(arr, colCount)
{
	str = "<table border=0>"
	for(var row in arr)
	{
		arrRow = arr[row].split(":");
		if (colCount && colCount == 1)
		{
			str += "<tr>"
				+ '<td width="20px"><input type="checkbox" id="chkShow_' + row + '" value="' + arrRow[0] + '" /></td>'
				+ "<td width='150px' align='left'><b>" + arrRow[1] + ":</b></td>"
				+ '<td width="260px">'
				+ '<span id="spanShow_' + row + '_value"></span></td>'
				+ "</tr>"
		}
		else
		{
			str += (parseInt(row) % 2 ? "" : "<tr>")
				+ '<td width="20px"><input type="checkbox" id="chkShow_' + row + '" value="' + arrRow[0] + '" /></td>'
				+ "<td width='80px' align='left'><b>" + arrRow[1] + ":</b></td>"
				+ '<td width="130px">'
				+ '<span id="spanShow_' + row + '_value"></span></td>'
				+ (parseInt(row) % 2 ? "</tr>" : "")
		}
	}
	str += "</table>"
	return str;
}

function createSelectHtml(arr, colCount)
{
	str = '<select name="sltShow" id="sltShow" style="width:360px;">';
	str += '<option value="">'+gettext('--- select ---')+'</option>'
	for(var row in arr)
	{
		if (colCount && colCount == 1)
		{
			str += '<option value="' + arr[row] + '">' + arr[row] + '&nbsp; </option>';
		}
		else
		{
			arrRow = arr[row].split(" ");
			str += '<option value="' + arrRow[0] + '">' + arrRow[1] + '&nbsp; ( ' + arrRow[0] + ' )</option>';
		}
	}
	str +='</select>';
	return str;
}

function IsSupportNewCSS()
{
	ua = navigator.userAgent;
	s = "MSIE";
	if ((i = ua.indexOf(s)) >= 0) {
		var version = parseFloat(ua.substr(i + s.length));
		if(version<7) return 0;
	}
	return 1;
}

function valiDate(str){                
    var reg = /^(\d+)-(\d{1,2})-(\d{1,2})$/;
    var r = str.match(reg);
    if(r==null)return false;
    r[2]=r[2]-1;
    var d= new Date(r[1], r[2],r[3]);
    if(d.getFullYear()!=r[1])return false;
    if(d.getMonth()!=r[2])return false;
    if(d.getDate()!=r[3])return false;
    return true;
}
function valiDateTimes(str){                
     var reg = /^(\d+)-(\d{1,2})-(\d{1,2}) (\d{1,2}):(\d{1,2}):(\d{1,2})$/;
     var r = str.match(reg);
     if(r==null)return false;
     r[2]=r[2]-1;
     var d= new Date(r[1], r[2],r[3], r[4],r[5], r[6]);
     if(d.getFullYear()!=r[1])return false;
	 if(d.getMonth()!=r[2])return false;
     if(d.getDate()!=r[3])return false;
     if(d.getHours()!=r[4])return false;
     if(d.getMinutes()!=r[5])return false;
     if(d.getSeconds()!=r[6])return false;
     return true;
 }

