var Library = Class.create({
  DOC_TYPE_SPHINX: 0,
  DOC_TYPE_EPYDOC: 1,

  initialize: function() {
    this.PACKAGES = [
      ["python",    this.DOC_TYPE_SPHINX, ["2.7.1"]],
      ["pyinotify", this.DOC_TYPE_EPYDOC, ["0.9.2"]]
    ];

    this.package_data = {};
    this.selected_packages = ["python-2.7.1", "pyinotify-0.9.2"];

    this.selected_packages.each(function(package) {
      var script = new Element('script', {
        'language': 'javascript',
        'src': '/static/data/' + package + '.js'
      });
      $$('body')[0].appendChild(script);
    });
  },

  register_package_data: function(nameversion, data) {
    this.package_data[nameversion] = data;
  },

  package_doc_type: function(nameversion) {
    var name = nameversion.substr(0, nameversion.indexOf("-"));
    var data = this.PACKAGES.find(function(x) { return x[0] == name; });
    return data[1];
  }
});


var SearchController = Class.create({
  BASE_URL: "static/doc/",
  TYPE_SORT_ORDER: [5, 4, 4, 4, 3, 2, 2, 2, 2, 1, 1, 1, 1],
  TYPE_CSS_CLASS:  ["mod", "class", "exception", "ctype", "cmacro",
                    "classmethod", "function", "method", "cfunction",
                    "data", "attribute", "cvar", "cmember"],

  initialize: function(library, input_element, results_element,
                       content_element, header_element) {
    this.library = library;
    this.input_element = input_element;
    this.results_element = results_element;
    this.content_element = content_element;
    this.header_element = header_element;

    this.ignore_next_hash_change = false;

    this.result_count = 0;

    // Listen for key events on the input box.
    this.input_element.observe('keyup', this.input_changed.bind(this));

    // Listen for key events on everything.
    document.observe('keydown', this.key_pressed.bind(this));

    // Listen for an event when the frame's URL changes.
    this.content_element.observe('load', this.content_frame_changed.bind(this));
    this.content_frame_changed();

    // Browse to the page the user put in the hash part of the URL.
    if (window.location.hash) {
      this.browse_to(window.location.hash);
      this.activate_selection();
    } else {
      this.search("");
    }

    this.input_element.focus();
  },

  input_changed: function(event) {
    this.search(this.input_element.value, true);
  },

  search: function(search_text, highlight) {
    // Don't do anything if the text wasn't changed since last time.
    if (search_text == this.search_text)
      return;
    this.search_text = search_text;
    this.selected_result = -1;
    this.result_count = 0;

    // Split the text into tokens, ignoring empty ones.
    var tokens = search_text.toLowerCase().split(" ").reject(function(x) { return x.blank(); });
    var tokens_len = tokens.length;

    // This regex will highlight the search terms in the matches.
    var highlight_regexp = new RegExp("(" + tokens.join("|") + ")", "gi");

    // Store results in here.
    var results = [];

    var packages_count = this.library.selected_packages.length;
    for (var i=0 ; i<packages_count ; ++i) {
      var package = this.library.selected_packages[i];
      var data = this.library.package_data[package];
      if (data == undefined) {
        continue;
      }

      var package_base_url = this.BASE_URL + package + "/";

      var len = data.length;
      for (var j=0 ; j<len && results.length<500 ; ++j) {
        var result_name_lower = data[j][0];

        // Does it match the search text?
        // The rules are:
        //  * If any token isn't found in the symbol name, abort.
        //  * Otherwise, for each token increment the score by:
        //     +2 if the match was at the beginning or after a period
        //     +1 if the case matched exactly
        var token_didnt_match = false;
        var overall_score = 0;

        if (tokens.length > 0) {
          for (var k=0 ; k<tokens_len ; ++k) {
            var index = result_name_lower.indexOf(tokens[k]);
            if (index == -1) {
              // If it didn't match at all then short circuit the scoring and
              // skip the other tokens.
              token_didnt_match = true;
              break;
            }

            var score = 0;

            // Matched at the beginning or after a period?
            if (index == 0 || result_name_lower.charAt(index-1) == '.') {
              score += 2;
            }

            // Case matched?
            if (data[j][1].substring(index, index + tokens[k].length) == tokens[k]) {
              score += 1;
            }

            overall_score = Math.max(overall_score, score);
          }

          // Didn't match?
          if (token_didnt_match)
            continue;
        }

        // Get information about this symbol
        var result = {
          name:        data[j][1],
          type:        data[j][2],
          destination: data[j][3],
        };

        // Highlight the search terms in the result
        var highlighted_name = result.name;
        if (highlight && tokens.length != 0) {
          highlighted_name = highlighted_name.replace(
            highlight_regexp, '<span class="highlight">$1</span>');
        }

        // Construct the URL
        result.url = package_base_url + result.destination;

        // Add to the list of results
        var html = '<li class="' + this.TYPE_CSS_CLASS[result.type] + '">' +
                   '<a target="contentframe" href="' + result.url + '">' +
                   highlighted_name + '</a></li>';

        results.push([
          overall_score * 10 + this.TYPE_SORT_ORDER[result.type],
          result_name_lower,
          html
        ]);
      }
    }

    // Sort all results by score, then alphabetically
    results.sort(function(a, b) {
      if (a[0] < b[0]) return 1;
      if (a[0] > b[0]) return -1;
      return (a[1] < b[1]) ? -1 : (a[1] > b[1]) ? 1 : 0;
    });

    // Make the list and insert it into the DOM
    var html = "";
    results.each(function(result) {
      html += result[2];
    });

    var ul = new Element("ul");
    ul.innerHTML = html;
    ul.observe('click', this.result_clicked.bind(this));

    this.result_count = results.length;
    this.results_element.update(ul);
  },

  result_clicked: function(event) {
    var li = event.findElement("li");
    if (li == document)
      return;

    this.set_selection(this.get_result_index(li));
    this.activate_li(li);
  },

  key_pressed: function(event) {
    if (event.altKey || event.ctrlKey)
      return;

    var element = Event.findElement(event);

    switch (event.keyCode) {
      case Event.KEY_UP:
        this.move_selection(-1);
        break;

      case Event.KEY_DOWN:
        this.move_selection(+1);
        break;

      case Event.KEY_RETURN:
        this.activate_selection();
        break;

      case Event.KEY_ESC:
        this.input_element.focus();
        this.input_element.select();
        break;

      default:
        if (event.keyCode >= 65 && event.keyCode <= 90 && element != this.input_element) {
          var char = String.fromCharCode(event.keyCode);
          if (!event.shiftKey)
            char = char.toLowerCase();

          // Stop the event before focusing the input box or it'll be added
          // twice.
          Event.stop(event);
          this.input_element.value += char;
          this.input_element.focus();
        }
        return;
    }

    Event.stop(event);
  },

  get_result_li: function(index) {
    return this.results_element.select("li")[index];
  },

  get_result_index: function(li) {
    var all = this.results_element.select("li");
    var len = all.length;
    for (var i=0 ; i<len ; ++i) {
      if (all[i] == li)
        return i;
    }
    return null;
  },

  move_selection: function(delta) {
    if (this.selected_result == -1) {
      this.set_selection(0);
    } else {
      this.set_selection(this.selected_result + delta);
    }
  },

  set_selection: function(index) {
    if (this.result_count == 0)
      return;

    if (this.selected_result != -1) {
      // Deselect the old element
      var element = this.get_result_li(this.selected_result);
      element.removeClassName("selected");
    }

    // Restrict the selection to the size of the result set
    index = Math.max(0, Math.min(this.result_count-1, index));

    // Select the new element
    var element = this.get_result_li(index);
    element.addClassName("selected");

    this.selected_result = index;
  },

  activate_selection: function() {
    if (this.selected_result == -1) {
      this.move_selection(+1);
      if (this.selected_result == -1)
        return;
    }

    this.activate_li(this.get_result_li(this.selected_result));
  },

  activate_li: function(li) {
    this.ignore_next_hash_change = true;
    this.content_element.src = li.select("a")[0].href;
  },

  content_frame_changed: function(event) {
    var frame_window = this.content_element.contentWindow;
    var frame_document = frame_window.document;

    // Update the title
    var title = frame_document.title;
    this.header_element.update(title.escapeHTML());
    document.title = title;

    // Listen for keypresses on the new frame
    Event.observe(frame_document, 'keydown', this.key_pressed.bind(this));

    // Listen for hash changes
    Event.observe(frame_window, 'hashchange', this.content_hash_changed.bind(this));
    this.content_hash_changed();
  },

  content_hash_changed: function(event) {
    var path = this.content_element.contentWindow.location.pathname;
    var hash = this.content_element.contentWindow.location.hash;

    var path_regex = new RegExp("doc/([^/]+)/(.*)");
    var match = path_regex.exec(path);

    if (!match)
      return;

    var nameversion = match[1];
    var page = match[2];

    // Get the type of this package - how we handle URLs differs between
    // documentation systems
    var doc_type = this.library.package_doc_type(nameversion);

    var new_hash;
    if (doc_type == this.library.DOC_TYPE_SPHINX) {
      // All sphinx links have hashes
      if (!hash) {
        return;
      }

      // Take any module- prefix off module names.
      if (hash.startsWith("#module-"))
        new_hash = "#" + hash.substring(8);
      else
        new_hash = hash;
    } else if (doc_type == this.library.DOC_TYPE_EPYDOC) {
      // Epydoc links are the page name + "." + hash
      var dash = page.lastIndexOf("-");
      if (dash != -1) {
        page = page.substr(0, dash);
      }

      new_hash = "#" + page;
      if (hash) {
        new_hash += "." + hash.substr(1)
      }
    } else {
      // Unknown doc type
      return;
    }

    window.history.replaceState(new_hash, "", new_hash);

    if (this.ignore_next_hash_change) {
      this.ignore_next_hash_change = false;
      return;
    }

    this.browse_to(new_hash);
  },

  browse_to: function(name) {
    // Take the # off
    name = name.substring(1);

    // Find the top-level symbol name.
    var top_level_symbol = name;
    if (top_level_symbol.indexOf(".") != -1)
      top_level_symbol = top_level_symbol.substring(0, top_level_symbol.indexOf("."));

    // Try to find a documentation entry with this name
    var packages_count = this.library.selected_packages.length;
    for (var i=0 ; i<packages_count ; ++i) {
      var package = this.library.selected_packages[i];
      var data = this.library.package_data[package];
      if (data == undefined) {
        continue;
      }

      var len = data.length;
      for (var j=0 ; j<len ; ++j) {
        if (data[j][1] != name)
          continue;

        // Got one - do a search for the top-level symbol
        this.search(top_level_symbol, false);

        // Now select the right search result
        var results = this.results_element.select("li");
        var results_len = results.length;
        for (var j=0 ; j<results_len ; ++j) {
          if (results[j].down().innerText == name) {
            this.set_selection(j);
            break;
          }
        }

        return;
      }
    }
  }
});

var controller;
var library;

Event.observe(window, 'load', function() {
  library = new Library();
  controller = new SearchController(library,
    $("search"), $("searchresults"), $("contentframe"), $("contentheader"));
});
