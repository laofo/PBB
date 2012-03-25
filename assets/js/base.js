readySubmit=false;

function checkInput(id,bool)
{
    if(bool)
    {
        readySubmit=false;
        $(id+"-g").addClass("error");
    }
    else
    {
        $(id+"-g").removeClass("error");
    }
}
function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

var args = {};
var query = location.search.substring(1);
// Get query string
var pairs = query.split("&");
// Break at ampersand
for(var i = 0; i < pairs.length; i++) {
    var pos = pairs[i].indexOf('=');
    // Look for "name=value"
    if (pos == -1) continue;
    // If not found, skip
    var argname = pairs[i].substring(0,pos);// Extract the name
    var value = pairs[i].substring(pos+1);// Extract the value
    value = decodeURIComponent(value);// Decode it, if needed
    args[argname] = value;
    // Store as a property
}
var sUrl = document.URL;
var domain = sUrl.slice(sUrl.indexOf('://')+3, sUrl.indexOf('/', sUrl.indexOf('://')+3));

function adjustOffset(el, offset) {
    /* From http://stackoverflow.com/a/8928945/611741 */
    var val = el.value, newOffset = offset;
    if (val.indexOf("\r\n") > -1) {
        var matches = val.replace(/\r\n/g, "\n").slice(0, offset).match(/\n/g);
        newOffset += matches ? matches.length : 0;
    }
    return newOffset;
}

$.fn.setCursorPosition = function(position){
    /* From http://stackoverflow.com/a/7180862/611741 */
    if(this.lengh == 0) return this;
    return $(this).setSelection(position, position);
}

$.fn.setSelection = function(selectionStart, selectionEnd) {
    /* From http://stackoverflow.com/a/7180862/611741
     modified to fit http://stackoverflow.com/a/8928945/611741 */
    if(this.lengh == 0) return this;
    input = this[0];

    if (input.createTextRange) {
        var range = input.createTextRange();
        range.collapse(true);
        range.moveEnd('character', selectionEnd);
        range.moveStart('character', selectionStart);
        range.select();
    } else if (input.setSelectionRange) {
        input.focus();
        selectionStart = adjustOffset(input, selectionStart);
        selectionEnd = adjustOffset(input, selectionEnd);
        input.setSelectionRange(selectionStart, selectionEnd);
    }

    return this;
}

$.fn.focusEnd = function(){
    /* From http://stackoverflow.com/a/7180862/611741 */
    this.setCursorPosition(this.val().length);
}

var isChrome = navigator.userAgent.indexOf("Chrome") !== -1

var init_article = function(){
    $('pre>code').each(function(i, e) {hljs.highlightBlock(e, '    ')});
    all_link = $('article a');
    for(var i=0;all_link[i];i++){
        link = all_link[i];
        link_url = link.href;
        if (link_url.indexOf(".png") !== -1 || link_url.indexOf(".jpg") !== -1 || link_url.indexOf(".gif") !== -1){
            var img = $('<img src="'+all_link[i].href+'" />');
            img.insertBefore(link);
            link.parentNode.removeChild(link);
        }
    }
}
$(function() {
    $("#new_reply").live("ajax:success",
        function() {
            $(this).find("textarea").val("")
        }).live("ajax:error",
        function(a, b, c) {
            var d = $('<div class="alert-message error fade in"><a href="#" class="close">×</a><p></p></div>').alert();
            d.find("p").text(b.responseText),
                d.hide().prependTo($(this)).fadeIn("fast")
        }),
        $(".at").live("click",
            function(a) {
                var b = $("#wmd-input");
                b.focus().val(b.val() + "@" + $(this).data("user-name") + " "),
                    a.preventDefault()
            })
    $('time').timeago();
    $("a[rel=popover]").popover()
    if (navigator.userAgent.indexOf("Kindle") == -1)
        $(".item-list a").attr('target','_blank');
    init_article();
    var doing = false;
    $("#mark").click(function(){
        if(doing)
            return false;
        if($("#mark-show").hasClass('icon-heart-empty')){
            doing=true;
            $.post("/topics/"+postID+"/mark",{_xsrf:$("input[name='_xsrf']").val()},
                function(data){
                    $("#mark-show").removeClass('icon-heart-empty');
                    $("#mark-show").addClass('icon-heart')
                    doing=false;
                    $('#markedpost').text((parseInt($('#markedpost').text())+1).toString());
                });
        }else{
            doing=true;
            $.post("/topics/"+postID+"/mark",{_xsrf:$("input[name='_xsrf']").val()},
                function(data){
                    $("#mark-show").addClass('icon-heart-empty');
                    $("#mark-show").removeClass('icon-heart')
                    doing=false;
                    $('#markedpost').text((parseInt($('#markedpost').text())-1).toString());
                });
        }
        return false;
    });

    if (islogin){
        if (isadmin){
            $('.kill').removeClass('hide');
            $('#changetag-link').removeClass('hide');

        }
        all_user = $('#comments a[rel=popover]');
        for(var i=0;all_user[i];i++){
            user = $(all_user[i]);
            if (block_user.indexOf('.'+user.html()+'.') !== -1)
                user.parents('tr').hide();
        }
    }
    $('.kill').click(
        function(){
            if (confirm("真的要和谐么"))
                $.get($(this).attr('href')).success(function(){location.href="/";}).error(function() { alert("和谐中出现错误，重试一下呗？"); });
            return false;
        }
    );
    $('#comments .kill').click(
        function(){
            if (confirm("真的要和谐么"))
                $.get($(this).attr('href')).success(function(){location.reload();}).error(function() { alert("和谐中出现错误，重试一下呗？"); });
            return false;
        }
    );
    $("#tweetsubmit").click(function(){
        if ($("#tweetcontent").val() == "")
            return false;
        $("#tweet").modal('hide');
        $.post("/twitter/tweet",{
                tweet:$("#tweetcontent").val()},
            function(data){
                $("#tweetcontent").val("");
            },"json");
        return false;
    });
    document.onkeyup=function(event) {
        if(window.ActiveXObject) {
            var keydown = window.event.keyCode;
            event=window.event;
        }else{
            var keydown = event.keyCode;
            if(event.ctrlKey && keydown == 13){
                if ($('body').hasClass('modal-open'))
                    $('#tweetsubmit').click();
                else
                    $('#submit').click();
            }
        }
    };
    $('#search_form').submit(function(e){
        e.preventDefault();
        search();
    });

    function search(){
        var q = document.getElementById('q');
        if (q.value != '')
            window.open('http://www.google.com/search?q=site:' + domain + ' ' + q.value, '_blank');
        return false;
    }
});