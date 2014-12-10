// Inserts shortcut buttons after all of the following:
//     <input type="text" class="vDateField">
//     <input type="text" class="vTimeField">

var DateTimeShortcuts = {
    calendars: [],
    calendarInputs: [],
    clockInputs: [],
    calendarDivName1: 'calendarbox', // name of calendar <div> that gets toggled
    calendarDivName2: 'calendarin',  // name of <div> that contains calendar
    calendarLinkName: 'calendarlink',// name of the link that is used to toggle
    clockDivName: 'clockbox',        // name of clock <div> that gets toggled
    clockLinkName: 'clocklink',      // name of the link that is used to toggle
    admin_media_prefix: '',
    init: function() {    	
        // Deduce admin_media_prefix by looking at the <script>s in the
        // current document and finding the URL of *this* module.
        var scripts = document.getElementsByTagName('script');
        for (var i=0; i<scripts.length; i++) {
            if (scripts[i].src.match(/DateTimeShortcuts/)) {
                var idx = scripts[i].src.indexOf('jslib/DateTimeShortcuts');
                DateTimeShortcuts.admin_media_prefix = scripts[i].src.substring(0, idx);
                break;
            }
        }
		$("._pop_time_").remove();
        var inputs = $("input.vTimeField");
        for (i=0; i<inputs.length; i++) 
            	DateTimeShortcuts.addClock(inputs[i]);
        var inputs = $("input.vDateOnlyField");
		inputs.removeClass('vDateField');
        for (i=0; i<inputs.length; i++) 
            	DateTimeShortcuts.addCalendar(inputs[i]);
        var inputs = $("input.vDateField");
        for (i=0; i<inputs.length; i++) {
            	DateTimeShortcuts.addClock(inputs[i]);
                DateTimeShortcuts.addCalendar(inputs[i]);                
            }
    },
    // Add clock widget to a given field
    addClock: function(inp) {
        var num = DateTimeShortcuts.clockInputs.length;
        DateTimeShortcuts.clockInputs[num] = inp;

        // Shortcut links (clock icon and "Now" link)
        var shortcuts_span = document.createElement('span');
		shortcuts_span.className="_pop_time_";
        inp.parentNode.insertBefore(shortcuts_span, inp.nextSibling);
        var now_link = document.createElement('a');
        now_link.setAttribute('href', "javascript:DateTimeShortcuts.handleClockQuicklink(" + num + ", new Date().getHourMinuteSecond());");
        now_link.appendChild(document.createTextNode(gettext('Now')));
        var clock_link = document.createElement('a');
        clock_link.setAttribute('href', 'javascript:DateTimeShortcuts.openClock(' + num + ');');
        clock_link.id = DateTimeShortcuts.clockLinkName + num;
        quickElement('img', clock_link, '', 'src', DateTimeShortcuts.admin_media_prefix + 'img/icon_clock.gif', 'alt', gettext('Clock'));
        shortcuts_span.appendChild(document.createTextNode('\240'));
        shortcuts_span.appendChild(now_link);
        shortcuts_span.appendChild(document.createTextNode('\240|\240'));
        shortcuts_span.appendChild(clock_link);

        var clock_box = document.createElement('div');
        clock_box.style.display = 'none';
        clock_box.style.position = 'absolute';
        clock_box.className = 'clockbox module';
        clock_box.setAttribute('id', DateTimeShortcuts.clockDivName + num);
        document.body.appendChild(clock_box);
        addEvent(clock_box, 'click', DateTimeShortcuts.cancelEventPropagation);

        quickElement('h2', clock_box, gettext('Choose a time'));
        time_list = quickElement('ul', clock_box, '');
        time_list.className = 'timelist';
        quickElement("a", quickElement("li", time_list, ""), gettext("Now"), "href", "javascript:DateTimeShortcuts.handleClockQuicklink(" + num + ", new Date().getHourMinuteSecond());");
//        quickElement("a", quickElement("li", time_list, ""), gettext("Midnight"), "href", "javascript:DateTimeShortcuts.handleClockQuicklink(" + num + ", '24:00:00');");
        quickElement("a", quickElement("li", time_list, ""), gettext("6 a.m."), "href", "javascript:DateTimeShortcuts.handleClockQuicklink(" + num + ", '06:00:00');");
        quickElement("a", quickElement("li", time_list, ""), gettext("Noon"), "href", "javascript:DateTimeShortcuts.handleClockQuicklink(" + num + ", '12:00:00');");

        cancel_p = quickElement('p', clock_box, '');
        cancel_p.className = 'calendar-cancel';
        quickElement('a', cancel_p, gettext('Cancel'), 'href', 'javascript:DateTimeShortcuts.dismissClock(' + num + ');');
    },
    openClock: function(num) {
        var clock_box = document.getElementById(DateTimeShortcuts.clockDivName+num)
        var clock_link = document.getElementById(DateTimeShortcuts.clockLinkName+num)
    
        // Recalculate the clockbox position
        // is it left-to-right or right-to-left layout ?
        if (getStyle(document.body,'direction')!='rtl') {
            if(findPosX(clock_link)>800)
                clock_box.style.left = findPosX(clock_link)-17 + 'px';
            else
                clock_box.style.left = findPosX(clock_link) + 17 + 'px';
        }
        else {
            // since style's width is in em, it'd be tough to calculate
            // px value of it. let's use an estimated px for now
            // TODO: IE returns wrong value for findPosX when in rtl mode
            //       (it returns as it was left aligned), needs to be fixed.
            clock_box.style.left = findPosX(clock_link) - 110 + 'px';
        }
        clock_box.style.top = findPosY(clock_link) - 30 + 'px';
    
        // Show the clock box
        clock_box.style.display = 'block';
        addEvent(window, 'click', function() { DateTimeShortcuts.dismissClock(num); return true; });
    },
    dismissClock: function(num) {
       document.getElementById(DateTimeShortcuts.clockDivName + num).style.display = 'none';
       window.onclick = null;
    },
    handleClockQuicklink: function(num, val) {    	
		str = DateTimeShortcuts.clockInputs[num].value
		if("vTimeField"==DateTimeShortcuts.clockInputs[num].className)
			DateTimeShortcuts.clockInputs[num].value=val
		else
		{
			nbsp_index = str.indexOf(' ');
			DateTimeShortcuts.clockInputs[num].value = ((nbsp_index > -1)?str.substring(0,nbsp_index):str) + ' ' + val;
		}
       	DateTimeShortcuts.dismissClock(num);
    },
    // Add calendar widget to a given field.
    addCalendar: function(inp) {
        var num = DateTimeShortcuts.calendars.length;

        DateTimeShortcuts.calendarInputs[num] = inp;

        // Shortcut links (calendar icon and "Today" link)
        var shortcuts_span = document.createElement('span');
        inp.parentNode.insertBefore(shortcuts_span, inp.nextSibling);
        var today_link = document.createElement('a');
        today_link.setAttribute('href', 'javascript:DateTimeShortcuts.handleCalendarQuickLink(' + num + ', 0);');
        today_link.appendChild(document.createTextNode(gettext('Today')));
        var cal_link = document.createElement('a');
        cal_link.setAttribute('href', 'javascript:DateTimeShortcuts.openCalendar(' + num + ');');
        cal_link.id = DateTimeShortcuts.calendarLinkName + num;
        quickElement('img', cal_link, '', 'src', DateTimeShortcuts.admin_media_prefix + 'img/icon_calendar.gif', 'alt', gettext('Calendar'));
        shortcuts_span.appendChild(document.createTextNode('\240'));
        shortcuts_span.appendChild(today_link);
        shortcuts_span.appendChild(document.createTextNode('\240|\240'));
        shortcuts_span.appendChild(cal_link);

        var cal_box = document.createElement('div');
        cal_box.style.display = 'none';
        cal_box.style.position = 'absolute';
        cal_box.className = 'calendarbox module';
        cal_box.setAttribute('id', DateTimeShortcuts.calendarDivName1 + num);
        document.body.appendChild(cal_box);
        addEvent(cal_box, 'click', DateTimeShortcuts.cancelEventPropagation);

        // next-prev links
        var cal_nav = quickElement('div', cal_box, '');
        var cal_nav_prev = quickElement('a', cal_nav, '<', 'href', 'javascript:DateTimeShortcuts.drawPrev('+num+');');
        cal_nav_prev.className = 'calendarnav-previous';
        var cal_nav_next = quickElement('a', cal_nav, '>', 'href', 'javascript:DateTimeShortcuts.drawNext('+num+');');
        cal_nav_next.className = 'calendarnav-next';

        // main box
        var cal_main = quickElement('div', cal_box, '', 'id', DateTimeShortcuts.calendarDivName2 + num);
        cal_main.className = 'calendar';
        DateTimeShortcuts.calendars[num] = new Calendar(DateTimeShortcuts.calendarDivName2 + num, DateTimeShortcuts.handleCalendarCallback(num));
        DateTimeShortcuts.calendars[num].drawCurrent();

        // calendar shortcuts
        var shortcuts = quickElement('div', cal_box, '');
        shortcuts.className = 'calendar-shortcuts';
        quickElement('a', shortcuts, gettext('Yesterday'), 'href', 'javascript:DateTimeShortcuts.handleCalendarQuickLink(' + num + ', -1);');
        shortcuts.appendChild(document.createTextNode('\240|\240'));
        quickElement('a', shortcuts, gettext('Today'), 'href', 'javascript:DateTimeShortcuts.handleCalendarQuickLink(' + num + ', 0);');
        shortcuts.appendChild(document.createTextNode('\240|\240'));
        quickElement('a', shortcuts, gettext('Tomorrow'), 'href', 'javascript:DateTimeShortcuts.handleCalendarQuickLink(' + num + ', +1);');

        // cancel bar
        var cancel_p = quickElement('p', cal_box, '');
        cancel_p.className = 'calendar-cancel';
        quickElement('a', cancel_p, gettext('Cancel'), 'href', 'javascript:DateTimeShortcuts.dismissCalendar(' + num + ');');
		shortcuts_span.className="_pop_cal_";
    },
    openCalendar: function(num) {
        var cal_box = document.getElementById(DateTimeShortcuts.calendarDivName1+num)
        var cal_link = document.getElementById(DateTimeShortcuts.calendarLinkName+num)
    
        // Recalculate the clockbox position
        // is it left-to-right or right-to-left layout ?
      
        if (getStyle(document.body,'direction')!='rtl') {
            if(findPosX(cal_link)>800)
                cal_box.style.left = findPosX(cal_link)-150 + 'px';
            else
                cal_box.style.left = findPosX(cal_link) + 17 + 'px';
        }
        else {
            // since style's width is in em, it'd be tough to calculate
            // px value of it. let's use an estimated px for now
            // TODO: IE returns wrong value for findPosX when in rtl mode
            //       (it returns as it was left aligned), needs to be fixed.
            cal_box.style.left = findPosX(cal_link) - 180 + 'px';
        }
        if(findPosY(cal_link)<100)
            cal_box.style.top = findPosY(cal_link) + 'px';
        else
            cal_box.style.top = findPosY(cal_link) - 75 + 'px';
    
        cal_box.style.display = 'block';
        addEvent(window, 'click', function() { DateTimeShortcuts.dismissCalendar(num); return true; });
    },
    dismissCalendar: function(num) {
        document.getElementById(DateTimeShortcuts.calendarDivName1+num).style.display = 'none';
    },
    drawPrev: function(num) {
        DateTimeShortcuts.calendars[num].drawPreviousMonth();
    },
    drawNext: function(num) {
        DateTimeShortcuts.calendars[num].drawNextMonth();
    },
    handleCalendarCallback: function(num) {
        return "function(y, m, d) { var str=DateTimeShortcuts.calendarInputs["+num+"].value;"
        	+ "var nbsp_index = str.indexOf(' ');"
			+ "var timeStr=(nbsp_index>-1)?str.substring(nbsp_index+1):'';"
        	+ "DateTimeShortcuts.calendarInputs["+num+"].value = y+'-'+(m<10?'0'+m:m)+'-'+(d<10?'0'+d:d) + (nbsp_index>0?' ' + timeStr:'');"
        	+ "document.getElementById(DateTimeShortcuts.calendarDivName1+"+num+").style.display='none';}";
    },
    handleCalendarQuickLink: function(num, offset) {
       var d = new Date();
       d.setDate(d.getDate() + offset)       
       str=DateTimeShortcuts.calendarInputs[num].value;
       nbsp_index = str.indexOf(' ');
       DateTimeShortcuts.calendarInputs[num].value = d.getISODate() + ((nbsp_index>0)?' '+str.substring(nbsp_index+1): '');
       DateTimeShortcuts.dismissCalendar(num);
    },
    cancelEventPropagation: function(e) {
        if (!e) e = window.event;
        e.cancelBubble = true;
        if (e.stopPropagation) e.stopPropagation();
    }
}

addEvent(window, 'load', DateTimeShortcuts.init);

