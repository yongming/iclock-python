function getPageKey(key)
{
	var t=getKeyQuery('t');
	if(t!="")
		return key+"_"+(t.substr(2));
	else
		return key;
}

function list2Dict(list, indexs)
{
	var r={};
	var i;
	for(i=0;i<list.length-1;i+=2)
	{
		r[list[i]]=list[i+1];
		if(indexs!=undefined) indexs[list[i]]=i/2;
	}
	return r;
}

(function($){
		  
	$.addFlex = function(t,p)
	{

		if (t.grid) return false; //return if already exist	
		
		// apply default properties
		p = $.extend({
			 height: 'auto', //default height
			 width: 'auto', //auto width
			 minwidth: 30, //min width of columns
			 minheight: 180, //min height of columns
			 resizable: true, //resizable table
			 nowrap: true, //
			 nomsg: 'No items',
			 minColToggle: 1, //minimum allowed column to be hidden
			 showToggleBtn: true, //show or hide column toggle popup
			 hideOnSubmit: true,
			 autoload: true,
			 blockOpacity: 0.5,
			 onToggleCol: false,
			 sortname: false,
			 sortorder: "ascending",
			 fwidth: false,
			 fwIndexs: {},
			 onSubmit: false // using a custom populate function
		  }, p);

		$(t).width($(t).width()-80);
		if(!p.fwidth)
		{
			p.fwidth={};
			var fwc=$.cookie(getPageKey("_fw"));
//			alert(fwc);
			if(fwc) p.fwidth=list2Dict(fwc.split("\t"), p.fwIndexs);
		}
		var thead = $("thead:first",t).get(0);
		var tbd = $("tbody:first",t).get(0);
		$('tr:first th',thead).each( function(i){
			var w;
			if(!$(this).attr("abbr")) $(this).attr("abbr", "COL"+i);
			var k=$(this).attr("abbr");
			if(p.fwidth[k]!=undefined)
				w=Math.abs(parseInt(p.fwidth[k]));
			else
				w=$(this).width()-4;
			$(this).attr('width', w);
			$($("tr:first td", tbd).get(i)).attr('width', w);
		});//固定住列表宽度

		tbd=null;
		thead=null;

		$(t)
		.show() //show if hidden
		.attr({cellPadding: 0, cellSpacing: 0, border: 0})  //remove padding and spacing
		.removeAttr('width') //remove width properties
		.css('width', 'auto');
	
		if(!p.sortname){ 
			p.sortname=getKeyQuery("o"); 
			if(p.sortname.indexOf('o=')==0)
			{
				if(p.sortname.indexOf("-")==2)
				{
					p.sortorder="descending";
					p.sortname=p.sortname.substr(3);
				}
				else
				{
					p.sortorder="ascending";
					p.sortname=p.sortname.substr(2);
				}
			}
		}
		//create grid class
		var g = {
			hset : {},
			rePosDrag: function () 
			{
				var cdleft = 0 - this.hDiv.scrollLeft;
				if (this.hDiv.scrollLeft>0) cdleft -= Math.floor(p.cgwidth/2);
				$(g.cDrag).css({top:g.hDiv.offsetTop+1});
				var cdpad = this.cdpad;

				$('div',g.cDrag).hide();

				$('thead tr:first th:visible',this.hDiv).each
					(
					 function (i)
					 {
					 var n = i;//$('thead tr:first th:visible',g.hDiv).index(this);

					 var cdpos = parseInt($('div',this).width());
					 var ppos = cdpos;
					 if (cdleft==0) 
					 cdleft -= Math.floor(p.cgwidth/2); 

					 cdpos = cdpos + cdleft + cdpad;

					 $('div:eq('+n+')',g.cDrag).css({'left':cdpos+'px'}).show();

						 cdleft = cdpos;
						 }
					  );

			},
			fixHeight: function (newH) 
			{
				//newH = false;
				if (!newH) newH = $(g.bDiv).height();
				if(newH<p.minheight) newH=p.minheight;

				var hdHeight = $(this.hDiv).height();
				$('div',this.cDrag).each(
						function ()
						{
						$(this).height(newH+hdHeight);
						}
						);

				var nd = parseInt($(g.nDiv).height());

				if (nd>newH)
					$(g.nDiv).height(newH).width(200);
				else
					$(g.nDiv).height('auto').width('auto');

				$(g.block).css({height:newH,marginBottom:(newH * -1)});

				var hrH = g.bDiv.offsetTop + newH;
				if (p.height != 'auto' && p.resizable) hrH = g.vDiv.offsetTop;
				$(g.rDiv).css({height: hrH});

			},
			dragStart: function (dragtype,e,obj) 
					   {
						   //default drag function start
						   if (dragtype=='colresize') //column resize
						   {
							   $(g.nDiv).hide();$(g.nBtn).hide();
							   var n = $('div',this.cDrag).index(obj);
							   var ow = $('th:visible div:eq('+n+')',this.hDiv).width();
									   $(obj).addClass('dragging').siblings().hide();
									   $(obj).prev().addClass('dragging').show();

									   this.colresize = {startX: e.pageX, ol: parseInt(obj.style.left), ow: ow, n : n };
									   $('body').css('cursor','col-resize');
							 }
							 else if (dragtype=='vresize') //table resize
							 {
							 var hgo = false;
							 $('body').css('cursor','row-resize');
							 if (obj) 
							 {
							 hgo = true;
							 $('body').css('cursor','col-resize');
							 }
							 if (p.height==undefined || p.height=='auto')
							 {
							 p.height=$(g.bDiv).height();
							 $(g.bDiv).height(p.height);
							 $('table',g.bDiv).removeClass('autoht');
							 }

							 this.vresize = {h: p.height, 
								 sy: e.pageY, w: p.width, 
								 sx: e.pageX, hgo: hgo};
							 }
								     else if (dragtype=='colMove') //column header drag
									   {
										   $(g.nDiv).hide();$(g.nBtn).hide();
										   this.hset = $(this.hDiv).offset();
										   this.hset.right = this.hset.left + $('table',this.hDiv).width();
										   this.hset.bottom = this.hset.top + $('table',this.hDiv).height();
										   this.dcol = obj;
										   this.dcoln = $('th',this.hDiv).index(obj);

										   this.colCopy = document.createElement("div");
										   this.colCopy.className = "colCopy";
										   this.colCopy.innerHTML = obj.innerHTML;
										   if ($.browser.msie)
										   {
											   this.colCopy.className = "colCopy ie";
										   }


										   $(this.colCopy).css({position:'absolute',float:'left',display:'none', textAlign: obj.align});
										   $('body').append(this.colCopy);
										   $(this.cDrag).hide();

									   }

							   $('body').noSelect();

					   },
			dragMove: function (e) {
			
				if (this.colresize) //column resize
					{
						var n = this.colresize.n;
						var diff = e.pageX-this.colresize.startX;
						var nleft = this.colresize.ol + diff;
						var nw = this.colresize.ow + diff;
						if (nw > p.minwidth)
							{
								$('div:eq('+n+')',this.cDrag).css('left',nleft);
								this.colresize.nw = nw;
							}
					}
				else if (this.vresize) //table resize
					{
						var v = this.vresize;
						var y = e.pageY;
						var diff = y-v.sy;
						
						if (!p.defwidth) p.defwidth = p.width;
						
						if (p.width != 'auto' && !p.nohresize && v.hgo)
						{
							var x = e.pageX;
							var xdiff = x - v.sx;
							var newW = v.w + xdiff;
							if (newW > p.defwidth)
								{
									this.gDiv.style.width = newW + 'px';
									p.width = newW;
								}
						}
						
						var newH = v.h + diff;
						if ((newH > p.minheight || p.height < p.minheight) && !v.hgo)
							{
								this.bDiv.style.height = newH + 'px';
								p.height = newH;
								this.fixHeight(newH);
							}
						v = null;
					}
				else if (this.colCopy) {
					$(this.dcol).addClass('thMove').removeClass('thOver'); 
					if (e.pageX > this.hset.right || e.pageX < this.hset.left || e.pageY > this.hset.bottom || e.pageY < this.hset.top)
					{
						//this.dragEnd();
						$('body').css('cursor','move');
					}
					else 
					$('body').css('cursor','pointer');
					$(this.colCopy).css({top:e.pageY + 10,left:e.pageX + 20, display: 'block'});
				}													
			
			},
			dragEnd: function () {

				if (this.colresize)
					{
						var n = this.colresize.n;
						var nw = this.colresize.nw;

								$('th:visible div:eq('+n+')',this.hDiv).css('width',nw);
								$('tr',this.bDiv).each (
									function ()
										{
										$('td:visible div:eq('+n+')',this).css('width',nw);
										}
								);
								this.hDiv.scrollLeft = this.bDiv.scrollLeft;


						$('div:eq('+n+')',this.cDrag).siblings().show();
						$('.dragging',this.cDrag).removeClass('dragging');
						this.rePosDrag();
						this.fixHeight();
						this.colresize = false;
						this.saveFieldOpt();
					}
				else if (this.vresize)
					{
						this.vresize = false;
					}
				else if (this.colCopy)
					{
						$(this.colCopy).remove();
						if (this.dcolt != null)
							{
							
							
							if (this.dcoln>this.dcolt)
								
								$('th:eq('+this.dcolt+')',this.hDiv).before(this.dcol);
							else
								$('th:eq('+this.dcolt+')',this.hDiv).after(this.dcol);
							
							
							
							this.switchCol(this.dcoln,this.dcolt);
							$(this.cdropleft).remove();
							$(this.cdropright).remove();
							this.rePosDrag();
							
																			
							}
						
						this.dcol = null;
						this.hset = null;
						this.dcoln = null;
						this.dcolt = null;
						this.colCopy = null;
						
						$('.thMove',this.hDiv).removeClass('thMove');
						$(this.cDrag).show();
					}										
				$('body').css('cursor','default');
				$('body').noSelect(false);
			},
			saveFieldOpt: function(){
				var fwidth=[];
				$('thead th',g.hDiv).each(function(i){
					var fn=$(this).attr("abbr");
					fwidth[i*2]=(fn?fn:("COL"+i));
					var w=parseInt($("div", this).css("width"));
					if($(this).css("display")=="none") w=0-w;
					fwidth[i*2+1]=w;
					});
				$.cookie(getPageKey("_fw"), fwidth.join("\t"), {path: document.location.pathname, expires: 10*356 });							  
			},
			toggleCol: function(cid, visible, CancelSave) {
				
				var ncol = $("th[axis='col"+cid+"']",this.hDiv)[0];
				var n = $('thead th',g.hDiv).index(ncol);
				var cb = $('input[value='+cid+']',g.nDiv)[0];
				
				
				if (visible==null)
					{
						visible = ncol.hide;
					}
				
				
				
				if (cb && $('input:checked',g.nDiv).length<p.minColToggle && !visible) return false;
				
				if (visible)
					{
						ncol.hide = false;
						$(ncol).show();
						if(cb)cb.checked = true;
					}
				else
					{
						ncol.hide = true;
						$(ncol).hide();
						if(cb)cb.checked = false;
					}
					
						$('tbody tr',t).each
							(
								function ()
									{
										if (visible)
											$('td:eq('+n+')',this).show();
										else
											$('td:eq('+n+')',this).hide();
									}
							);							
				
				this.rePosDrag();
				
				if (p.onToggleCol) p.onToggleCol(cid,visible);
				if(CancelSave==undefined) 	this.saveFieldOpt();
				return visible;
			},
			switchCol: function(cdrag,cdrop, CancelSave) { //switch columns
				
				$('tbody tr',t).each
					(
						function ()
							{
								if (cdrag>cdrop)
									$('td:eq('+cdrop+')',this).before($('td:eq('+cdrag+')',this));
								else
									$('td:eq('+cdrop+')',this).after($('td:eq('+cdrag+')',this));
							}
					);
					
					//switch order in nDiv
/*					if (cdrag>cdrop)
						$('tr:eq('+cdrop+')',this.nDiv).before($('tr:eq('+cdrag+')',this.nDiv));
					else
						$('tr:eq('+cdrop+')',this.nDiv).after($('tr:eq('+cdrag+')',this.nDiv));
						
					if ($.browser.msie&&$.browser.version<7.0) $('tr:eq('+cdrop+') input',this.nDiv)[0].checked = true;	
*/					
					this.hDiv.scrollLeft = this.bDiv.scrollLeft;
					if(CancelSave==undefined) 	this.saveFieldOpt();	
			},			
			scroll: function() {
					this.hDiv.scrollLeft = this.bDiv.scrollLeft;
					this.rePosDrag();
			},
			setColProp: function()
			{
				//hide invisble cols, and switch cols
				if(p.fwidth)
				{
					$("thead th", g.hDiv).each(function(i)
					{
						var fn=$(this).attr("abbr");
						if(fn && p.fwidth[fn]<0)
						g.toggleCol(i, false, true);
					});
					var i=0;
					for(fn in p.fwidth)
					{
						i=p.fwIndexs[fn];
						if(i!=undefined)
						{
							var h=$("thead th:eq("+i+")", g.hDiv);
							if(h.attr("abbr")!=fn)
							{
								var th=$("thead th[abbr='"+fn+"']", g.hDiv);
								var n = $('thead th',g.hDiv).index(th[0]);
								h.before(th);
								g.switchCol(n, i, true);
							}
						}
					}
				}		
			},
			addCellProp: function ()
			{
				
					$('tbody tr td',g.bDiv).each
					(
						function ()
							{
									var tdDiv = document.createElement('div');
									var n = $('td',$(this).parent()).index(this);
									var pth = $('th:eq('+n+')',g.hDiv).get(0);
			
									if (pth!=null)
									{
							
									 $(tdDiv).css({textAlign:pth.align,width: $('div:first',pth)[0].style.width});
									 
									 if (pth.hide) $(this).css('display','none');
									 
									 }
									 
									 if (p.nowrap==false) $(tdDiv).css('white-space','normal');
									 
									 if (this.innerHTML=='') this.innerHTML = '&nbsp;';
									 
									 //tdDiv.value = this.innerHTML; //store preprocess value
									 tdDiv.innerHTML = this.innerHTML;
									 
									 var prnt = $(this).parent()[0];
									 var pid = false;
									 if (prnt.id) pid = prnt.id.substr(3);
									 
									 if (pth!=null)
									 {
									 if (pth.process) pth.process(tdDiv,pid);
									 }
									 
									$(this).empty().append(tdDiv).removeAttr('width'); //wrap content

									//add editable event here 'dblclick'

							}
					);
					
			},
			getCellDim: function (obj) // get cell prop for editable event
			{
				var ht = parseInt($(obj).height());
				var pht = parseInt($(obj).parent().height());
				var wt = parseInt(obj.style.width);
				var pwt = parseInt($(obj).parent().width());
				var top = obj.offsetParent.offsetTop;
				var left = obj.offsetParent.offsetLeft;
				var pdl = parseInt($(obj).css('paddingLeft'));
				var pdt = parseInt($(obj).css('paddingTop'));
				return {ht:ht,wt:wt,top:top,left:left,pdl:pdl, pdt:pdt, pht:pht, pwt: pwt};
			},
			addRowProp: function()
			{
					$('tbody tr',g.bDiv).each
					(
						function ()
							{
							$(this)
							.hover(
								function (e) 
									{ 
									if (g.multisel) 
										{
										$(this).toggleClass('trSelected'); 
										}
									},
								function () {}						
							)
							;
							
							if ($.browser.msie&&$.browser.version<7.0)
								{
									$(this)
									.hover(
										function () { $(this).addClass('trOver'); },
										function () { $(this).removeClass('trOver'); }
									)
									;
								}
							}
					);
					
					
			}
			};		
		
		//init divs
		g.gDiv = document.createElement('div'); //create global container
		g.hDiv = document.createElement('div'); //create header container
		g.bDiv = document.createElement('div'); //create body container
		g.vDiv = document.createElement('div'); //create grip
		g.rDiv = document.createElement('div'); //create horizontal resizer
		g.cDrag = document.createElement('div'); //create column drag
		g.block = document.createElement('div'); //creat blocker
		g.nDiv = document.createElement('div'); //create column show/hide popup
		g.nBtn = document.createElement('div'); //create column show/hide button
		g.iDiv = document.createElement('div'); //create editable layer
		g.tDiv = document.createElement('div'); //create toolbar
		g.sDiv = document.createElement('div');
		
		g.hTable = document.createElement('table');

		//set gDiv
		g.gDiv.className = 'flexigrid';
		if (p.width!='auto') g.gDiv.style.width = p.width + 'px';

		//add conditional classes
		if ($.browser.msie)
			$(g.gDiv).addClass('ie');
		
		if (p.novstripe)
			$(g.gDiv).addClass('novstripe');

		$(t).before(g.gDiv);
		$(g.gDiv)
		.append(t)
		;

		
		//set hDiv
		g.hDiv.className = 'hDiv';

		$(t).before(g.hDiv);

		//set hTable
		g.hTable.cellPadding = 0;
		g.hTable.cellSpacing = 0;
		$(g.hDiv).append('<div class="hDivBox"></div>');
		$('div',g.hDiv).append(g.hTable);
		var thead = $("thead:first",t).get(0);
		if (thead) $(g.hTable).append(thead);
		thead = null;
		$(g.hTable).css("width", "auto");
		var ci = 0;

		//setup thead			
			$('thead tr:first th',g.hDiv).each
			(
			 	function ()
					{
						var thdiv = document.createElement('div');
					
						if (this.hide) $(this).hide();
							
						$(this).attr('axis','col' + ci++);
							
						 $(thdiv).css({textAlign:this.align, width: this.width + 'px'});
						 thdiv.innerHTML = this.innerHTML;
						$(this).empty().append(thdiv).removeAttr('width');
						if ($(this).attr('abbr')==p.sortname) 
						{
							$("div", this).addClass(p.sortorder);
						}
						if(this.className!="class_select_col")
						$(this).mousedown(function (e) 
							{
								g.dragStart('colMove',e,this);
							})
						.hover(
							function(){
								if (!g.colresize&&!$(this).hasClass('thMove')&&!g.colCopy) $(this).addClass('thOver');
								
								if (g.colCopy) 
									{
									var n = $('th',g.hDiv).index(this);
									
									if (n==g.dcoln) return false;
									
									if (n<g.dcoln) $(this).append(g.cdropleft);
									else $(this).append(g.cdropright);
									
									g.dcolt = n;
									
									} else if (!g.colresize) {
										
									var nv = $('th:visible',g.hDiv).index(this);
									var onl = parseInt($('div:eq('+nv+')',g.cDrag).css('left'));
									var nw = parseInt($(g.nBtn).width()) + parseInt($(g.nBtn).css('borderLeftWidth'));
									nl = onl - nw + Math.floor(p.cgwidth/2);
									
									$(g.nDiv).hide();$(g.nBtn).hide();
									
									$(g.nBtn).css({'left':nl, top:g.hDiv.offsetTop, height: $(g.hDiv).height()-1}).show();
									var fn=$(this).attr("abbr");
									var o_asc=$("#id_order_asc");
									var o_desc=$("#id_order_desc");
									var o_no=$("#id_order_none");
									if(fn && fn.indexOf('COL')!=0)
									{
										o_asc.show(); o_desc.show(); o_no.show();
										$("a",o_asc).attr("href", repUrlKey("o", fn));
										$("a",o_desc).attr("href", repUrlKey("o", "-"+fn));
										$("a",o_no).attr("href", repUrlKey("o", false));
									}
									else
									{
										o_asc.hide(); o_desc.hide(); o_no.hide();
									}
									
									var ndw = parseInt($(g.nDiv).width());
									if(ndw>200) $(g.nDiv).css({width: "200px"});	
									$(g.nDiv).css({top:g.bDiv.offsetTop-2});
									if ((nl+ndw)>$(g.gDiv).width())
										$(g.nDiv).css('left',onl-ndw+1);
									else
										$(g.nDiv).css('left',nl);										
									}
									
							},
							function(){
								$(this).removeClass('thOver');

								if (g.colCopy) 
									{								
									$(g.cdropleft).remove();
									$(g.cdropright).remove();
									g.dcolt = null;
									}
							})
						; //wrap content
					}
			);


		//set bDiv
		g.bDiv.className = 'bDiv';
		$(t).before(g.bDiv);
		$(g.bDiv)
		.css({ height: (p.height=='auto') ? 'auto' : p.height+"px", "min-height": p.minheight})
		.scroll(function (e) {g.scroll()})
		.append(t)
		;
		
		if (p.height == 'auto') 
			{
			$('table',g.bDiv).addClass('autoht');
			}


		//add td properties
		g.addCellProp();
		
		//add row properties
		g.addRowProp();
		
		//set cDrag
		
		var cdcol = $('thead tr:first th:first',g.hDiv).get(0);
		
		if (cdcol != null)
		{		
			g.cDrag.className = 'cDrag';
			g.cdpad = 0;

			g.cdpad += (isNaN(parseInt($('div',cdcol).css('borderLeftWidth'))) ? 0 : parseInt($('div',cdcol).css('borderLeftWidth'))); 
			g.cdpad += (isNaN(parseInt($('div',cdcol).css('borderRightWidth'))) ? 0 : parseInt($('div',cdcol).css('borderRightWidth'))); 
			g.cdpad += (isNaN(parseInt($('div',cdcol).css('paddingLeft'))) ? 0 : parseInt($('div',cdcol).css('paddingLeft'))); 
			g.cdpad += (isNaN(parseInt($('div',cdcol).css('paddingRight'))) ? 0 : parseInt($('div',cdcol).css('paddingRight'))); 
			g.cdpad += (isNaN(parseInt($(cdcol).css('borderLeftWidth'))) ? 0 : parseInt($(cdcol).css('borderLeftWidth'))); 
			g.cdpad += (isNaN(parseInt($(cdcol).css('borderRightWidth'))) ? 0 : parseInt($(cdcol).css('borderRightWidth'))); 
			g.cdpad += (isNaN(parseInt($(cdcol).css('paddingLeft'))) ? 0 : parseInt($(cdcol).css('paddingLeft'))); 
			g.cdpad += (isNaN(parseInt($(cdcol).css('paddingRight'))) ? 0 : parseInt($(cdcol).css('paddingRight'))); 
      if ($.browser.msie) g.cdpad-=1; 
			$(g.bDiv).before(g.cDrag);

			var cdheight = $(g.bDiv).height();
			var hdheight = $(g.hDiv).height();

			$(g.cDrag).css({top: -hdheight + 'px'});

			$('thead tr:first th',g.hDiv).each
				(
				 function ()
				 {
				 var cgDiv = document.createElement('div');
				 $(g.cDrag).append(cgDiv);
				 if (!p.cgwidth) p.cgwidth = $(cgDiv).width();
				 $(cgDiv).css({height: cdheight + hdheight})
				 .mousedown(function(e){g.dragStart('colresize',e,this);})
				 ;
				 if ($.browser.msie&&$.browser.version<7.0)
				 {
				 g.fixHeight($(g.gDiv).height());
				 $(cgDiv).hover(
					 function () 
					 {
//					 g.fixHeight();
					 $(this).addClass('dragging') 
					 },
					 function () { if (!g.colresize) $(this).removeClass('dragging') }
					 );
				 }
				 }
			);

			//g.rePosDrag();

		}
		
		if (p.resizable) 
		{
		g.vDiv.className = 'vGrip';
		$(g.vDiv)
		.mousedown(function (e) { g.dragStart('vresize',e)})
		.html('<span></span>');
		$(g.bDiv).after(g.vDiv);
		}
		
		if (p.resizable && p.width !='auto' && !p.nohresize) 
		{
		g.rDiv.className = 'hGrip';
		$(g.rDiv)
		.mousedown(function (e) {g.dragStart('vresize',e,true);})
		.html('<span></span>')
		.css('height',$(g.gDiv).height())
		;
		if ($.browser.msie&&$.browser.version<7.0)
		{
			$(g.rDiv).hover(function(){$(this).addClass('hgOver');},function(){$(this).removeClass('hgOver');});
		}
		$(g.gDiv).append(g.rDiv);
		}
		
		//setup cdrops
		g.cdropleft = document.createElement('span');
		g.cdropleft.className = 'cdropleft';
		g.cdropright = document.createElement('span');
		g.cdropright.className = 'cdropright';

		//add block
		g.block.className = 'gBlock';
		var gh = $(g.bDiv).height();
		var gtop = g.bDiv.offsetTop;
		$(g.block).css(
		{
			width: g.bDiv.style.width,
			height: gh,
			background: 'white',
			position: 'relative',
			marginBottom: (gh * -1),
			zIndex: 1,
			top: gtop,
			left: '0px'
		}
		);
		$(g.block).fadeTo(0,p.blockOpacity);				
		
		g.setColProp();

		// add column control
		if ($('th',g.hDiv).length)
		{
				
			g.nDiv.className = 'nDiv';
			g.nDiv.innerHTML = "<table cellpadding='0' cellspacing='0' ><tbody></tbody></table>";
			$(g.nDiv).css(
			{
				marginBottom: (gh * -1),
				display: 'none',
				top: gtop
			}
			).noSelect()
			;
			$('tbody',g.nDiv).append(
					'<tr id="id_order_asc"><td width="16px"><img src="/media/img/hmenu-asc.gif" /></td><td><a href="#">'+gettext('Order Asc')+'</a></td></tr>'+
					'<tr id="id_order_desc"><td><img src="/media/img/hmenu-desc.gif" /></td><td><a href="#">'+gettext('Order Desc')+'</a></td></tr>'+
					'<tr id="id_order_none"><td>&nbsp;</td><td><a href="#">'+gettext('No Order')+'</a></td></tr>');

			var cn = 0;
			$('th div',g.hDiv).each
			(
			 	function ()
					{
						var kcol = $("th[axis='col" + cn + "']",g.hDiv)[0];
						var chk = 'checked="checked"';
						if (kcol && kcol.style.display=='none') chk = '';
						if (!(kcol && cn==0 && $(kcol).attr("class")=='class_select_col'))
							$('tbody',g.nDiv).append('<tr><td class="ndcol1"><input type="checkbox" '+ chk +' class="togCol" value="'+ cn +'" /></td><td class="ndcol2">'+$("div",kcol).html()+'</td></tr>');
						cn++;
					}
			);
		

			if ($.browser.msie&&$.browser.version<7.0)
				$('tr',g.nDiv).hover
				(
				 	function () {$(this).addClass('ndcolover');},
					function () {$(this).removeClass('ndcolover');}
				);
			
			$('td.ndcol2',g.nDiv).click
			(
			 	function ()
					{
						if ($('input:checked',g.nDiv).length<=p.minColToggle&&$(this).prev().find('input')[0].checked) return false;
						return g.toggleCol($(this).prev().find('input').val());
					}
			);
			
			$('input.togCol',g.nDiv).click
			(
			 	function ()
					{
						
						if ($('input:checked',g.nDiv).length<p.minColToggle&&this.checked==false) return false;
						$(this).parent().next().trigger('click');
						//return false;
					}
			);


			$(g.gDiv).prepend(g.nDiv);
			
			$(g.nBtn).addClass('nBtn')
			.html('<div></div>')
			.click
			(
			 	function ()
				{
			 		$(g.nDiv).toggle(); return true;
				}
			);
			
			if (p.showToggleBtn) $(g.gDiv).prepend(g.nBtn);
			
		}
		
		// add date edit layer
		$(g.iDiv)
		.addClass('iDiv')
		.css({display:'none'})
		;
		$(g.bDiv).append(g.iDiv);
		
		// add flexigrid events
		$(g.bDiv).hover(function(){$(g.nDiv).hide();$(g.nBtn).hide();},function(){if (g.multisel) g.multisel = false;});
		$(g.gDiv).hover(function(){},function(){$(g.nDiv).hide();$(g.nBtn).hide();});
	

		//add document events
		$(document)
		.mousemove(function(e){g.dragMove(e)})
		.mouseup(function(e){g.dragEnd()})
		.hover(function(){},function (){g.dragEnd()});
		
		//browser adjustments
		if ($.browser.msie && $.browser.version<7.0)
		{
			$('.hDiv,.bDiv,.mDiv,.pDiv,.vGrip,.tDiv, .sDiv',g.gDiv)
			.css({width: '100%'});
			$(g.gDiv).addClass('ie6');
			if (p.width!='auto') $(g.gDiv).addClass('ie6fullwidthbug');			
		} 
		
		g.rePosDrag();
		g.fixHeight();
		
		//make grid functions accessible
		t.p = p;
		t.grid = g;
		
		// load data
		if (p.url&&p.autoload) 
			{
			g.populate();
			}
		
		return t;		
	};

	var docloaded = false;

	$(document).ready(function () {docloaded = true} );

	$.fn.flexigrid = function(p) {

		return this.each( function() {
				if (!docloaded)
				{
					$(this).hide();
					var t = this;
					$(document).ready
					(
						function ()
						{
						$.addFlex(t,p);
						}
					);
				} else {
					$.addFlex(this,p);
				}
			});

	}; //end flexigrid

	$.fn.flexReload = function(p) { // function to reload grid

		return this.each( function() {
				if (this.grid&&this.p.url) this.grid.populate();
			});

	}; //end flexReload

	$.fn.flexOptions = function(p) { //function to update general options

		return this.each( function() {
				if (this.grid) $.extend(this.p,p);
			});

	}; //end flexOptions

	$.fn.flexToggleCol = function(cid,visible) { // function to reload grid

		return this.each( function() {
				if (this.grid) this.grid.toggleCol(cid,visible);
			});

	}; //end flexToggleCol

	$.fn.flexAddData = function(data) { // function to add data to grid

		return this.each( function() {
				if (this.grid) this.grid.addData(data);
			});

	};

	$.fn.noSelect = function(p) { //no select plugin by me :-)

		if (p == null) 
			prevent = true;
		else
			prevent = p;

		if (prevent) {
		
		return this.each(function ()
			{
				if ($.browser.msie||$.browser.safari) $(this).bind('selectstart',function(){return false;});
				else if ($.browser.mozilla) 
					{
						$(this).css('MozUserSelect','none');
						$('body').trigger('focus');
					}
				else if ($.browser.opera) $(this).bind('mousedown',function(){return false;});
				else $(this).attr('unselectable','on');
			});
			
		} else {

		
		return this.each(function ()
			{
				if ($.browser.msie||$.browser.safari) $(this).unbind('selectstart');
				else if ($.browser.mozilla) $(this).css('MozUserSelect','inherit');
				else if ($.browser.opera) $(this).unbind('mousedown');
				else $(this).removeAttr('unselectable','on');
			});
		
		}

	}; //end noSelect
		
})(jQuery);
