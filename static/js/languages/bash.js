hljs.LANGUAGES.bash=function(){var a={"true":1,"false":1},b={className:"variable",begin:"\\$([a-zA-Z0-9_]+)\\b"},c={className:"variable",begin:"\\$\\{(([^}])|(\\\\}))+\\}",contains:[hljs.C_NUMBER_MODE]},d={className:"string",begin:'"',end:'"',illegal:"\\n",contains:[hljs.BACKSLASH_ESCAPE,b,c],relevance:0},e={className:"test_condition",begin:"",end:"",contains:[d,b,c,hljs.C_NUMBER_MODE],keywords:{literal:a},relevance:0};return{defaultMode:{keywords:{keyword:{"if":1,then:1,"else":1,fi:1,"for":1,"break":1,"continue":1,"while":1,"in":1,"do":1,done:1,echo:1,exit:1,"return":1,set:1,declare:1},literal:a},contains:[{className:"shebang",begin:"(#!\\/bin\\/bash)|(#!\\/bin\\/sh)",relevance:10},hljs.HASH_COMMENT_MODE,hljs.C_NUMBER_MODE,d,b,c,hljs.inherit(e,{begin:"\\[ ",end:" \\]",relevance:0}),hljs.inherit(e,{begin:"\\[\\[ ",end:" \\]\\]"})]}}}();