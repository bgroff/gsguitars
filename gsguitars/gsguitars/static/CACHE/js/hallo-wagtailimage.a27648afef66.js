// Generated by CoffeeScript 1.7.1
(function() {
  (function($) {
    return $.widget("IKS.hallowagtailimage", {
      options: {
        uuid: '',
        editable: null
      },
      populateToolbar: function(toolbar) {
        var button, widget;
        widget = this;
        button = $('<span></span>');
        button.hallobutton({
          uuid: this.options.uuid,
          editable: this.options.editable,
          label: 'Images',
          icon: 'icon-picture',
          command: null
        });
        toolbar.append(button);
        return button.on("click", function(event) {
          var insertionPoint, lastSelection;
          lastSelection = widget.options.editable.getSelection();
          insertionPoint = $(lastSelection.endContainer).parentsUntil('.richtext').last();
          return ModalWorkflow({
            url: window.chooserUrls.imageChooser + '?select_format=true',
            responses: {
              imageChosen: function(imageData) {
                var elem;
                elem = $(imageData.html).get(0);
                lastSelection.insertNode(elem);
                if (elem.getAttribute('contenteditable') === 'false') {
                  insertRichTextDeleteControl(elem);
                }
                return widget.options.editable.element.trigger('change');
              }
            }
          });
        });
      }
    });
  })(jQuery);

}).call(this);
