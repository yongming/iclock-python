jQuery.fn.sfHover = function() {
  jQuery(this).hover(
    function() { jQuery(this).addClass("sfHover"); },
    function() { jQuery(this).removeClass("sfHover"); }
  )

  return this

}

jQuery.fn.sfFocus = function() {
  jQuery(this).each(function(i) {
    jQuery(this).bind("focus", function() { jQuery(this).addClass('sfFocus');});
    jQuery(this).bind("blur", function() { jQuery(this).removeClass('sfFocus'); });
  });
  return this;
}

jQuery.fn.sfActive = function() {
    jQuery(this).each(function(i) {
      jQuery(this).mousedown (
        function() { jQuery(this).addClass('sfActive');}
      )
      jQuery(this).mouseup (
        function() { $(this).removeClass('sfActive');  }
      )
    });
    return this;
}

jQuery.fn.sfTarget = function() {
    jQuery(this).each(function(i) {
      jQuery(this).click(
        function() {
          jQuery(".sfTarget").removeClass('sfTarget');
          elem = jQuery(this).attr("href");
          if(elem) {
            jQuery(elem).addClass('sfTarget');
          }
          return this
        }
      )
    });
    return this;
}