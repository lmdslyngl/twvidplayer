
Vue.component("searchbox", {
  data: function() {
    return {
      searchText: ""
    };
  },
  mounted: function() {
    this.$nextTick(() => {
      document.getElementById("search-text").focus();
    });
  },
  methods: {
    onSearchClicked: function(evt) {
      if( this.searchText !== "" ) {
        this.$emit("on-search-clicked", this.searchText);
      }
    }
  },
  template: `
    <div class="searchbox">
      <div class="uk-search uk-search-default uk-width-1-1">
        <span uk-search-icon></span>
        <input
            id="search-text"
            class="uk-search-input"
            type="search"
            placeholder="Twitterで検索..."
            v-model="searchText"
            v-on:keyup.enter="onSearchClicked">
      </div>
      <button
          class="uk-button uk-button-primary"
          v-on:click="onSearchClicked">
        Search
      </button>
    </div>
  `
});

Vue.component("player-video", {
  props: ["videoUrl"],
  methods: {
    onPlayable: function() {
      let videoElem = document.getElementsByTagName("video")[0];
      videoElem.play();
    },
    onEnded: function() {
      this.$emit("ended");
    }
  },
  template: `
    <div class="vid">
      <video
        v-bind:src="videoUrl"
        v-on:loadeddata="onPlayable"
        v-on:ended="onEnded"
        playsinline controls />
    </div>
  `
});

Vue.component("player-soundcloud", {
  props: ["url"],
  data: function() {
    return {
      iframeHtml: ""
    }
  },
  mounted: function() {
    this.updateIFrameHtml();
  },
  methods: {
    updateIFrameHtml: function() {
      this.fetchIFrameHtml(this.url)
        .then((html) => {
          this.iframeHtml = html;
          this.$nextTick(() => {
            // 次のフレーム（iframeが追加されたとき）に
            // SoundCloudWidgetのイベントのバインドを行う
            this.bindPlayerEvent();
          });
        }).catch(() => {
          this.iframeHtml = "";
        });
    },
    fetchIFrameHtml: function(url) {
      return axios.get("https://soundcloud.com/oembed", {
        params: {
          format: "json",
          url: url,
          maxheight: "400"
        }
      }).then((response) => {
        return Promise.resolve(response.data["html"]);
      });
    },
    bindPlayerEvent: function() {
      let widgetElem = document.querySelector(".vid iframe");
      let widget = SC.Widget(widgetElem);
      widget.bind(SC.Widget.Events.READY, this.onPlayable);
      widget.bind(SC.Widget.Events.FINISH, this.onEnded);
    },
    onPlayable: function() {
      let widgetElem = document.querySelector(".vid iframe");
      let widget = SC.Widget(widgetElem);
      widget.play();
    },
    onEnded: function() {
      this.$emit("ended");
    }
  },
  watch: {
    url: function() {
      this.updateIFrameHtml();
    }
  },
  template: `
    <div class="vid" v-html="iframeHtml"></div>
  `
});

Vue.component("player-youtube", {
  props: ["url"],
  data: function() {
    return {
      player: null
    }
  },
  mounted: function() {
    this.updateYoutubeIFrame();
  },
  beforeDestroy: function() {
    this.player.stopVideo();
    this.player.clearVideo();
    this.player = null;
  },
  methods: {
    updateYoutubeIFrame: function() {
      if( this.player === null ) {
        this.player = new YT.Player("player-youtube", {
          height: "400",
          width: "640",
          videoId: this.videoId,
          events: {
            "onReady": this.onPlayable,
            "onStateChange": this.onStateChange,
            "onError": this.onError
          }
        });
      } else {
        this.player.loadVideoById({ videoId: this.videoId });
      }
    },
    onPlayable: function(evt) {
      this.player.playVideo();
    },
    onStateChange: function(evt) {
      if( evt.data === YT.PlayerState.ENDED ) {
        this.$emit("ended");
      }
    },
    onError: function(evt) {
      this.$emit("ended");
    }
  },
  computed: {
    videoId: function() {
      let urlObj = new URL(this.url);
      return urlObj.searchParams.get("v");
    }
  },
  watch: {
    url: function() {
      this.updateYoutubeIFrame();
    }
  },
  template: `
    <div class="vid">
      <div id="player-youtube"></div>
    </div>
  `
});

Vue.component("player", {
  props: ["url", "videoType"],
  methods: {
    onEnded: function() {
      this.$emit("ended");
    }
  },
  template: `
    <div class="player">
      <player-video
        v-bind:video-url="url"
        v-if="videoType === 'video'"
        v-on:ended="onEnded">
      </player-video>
      <player-soundcloud
        v-bind:url="url"
        v-if="videoType === 'soundcloud'"
        v-on:ended="onEnded">
      </player-soundcloud>
      <player-youtube
        v-bind:url="url"
        v-if="videoType === 'youtube'"
        v-on:ended="onEnded">
      </player-youtube>
    </div>
  `
});

Vue.component("pager", {
  methods: {
    onPrevClicked: function(evt) {
      this.$emit("on-prev-clicked");
    },
    onNextClicked: function(evt) {
      this.$emit("on-next-clicked");
    }
  },
  template: `
    <div class="control">
      <button
          class="uk-button uk-button-default"
          v-on:click="onPrevClicked">
        前へ
      </button>
      <div></div>
      <button
          class="uk-button uk-button-primary"
          v-on:click="onNextClicked">
        次へ
      </button>
    </div>
  `
});

Vue.component("tweet", {
  props: [
    "text",
    "author",
    "authorScreenName",
    "authorThumbnailUrl",
    "tweetUrl"
  ],
  computed: {
    textHtml: function() {
      return this.text.replace("\n", "<br>");
    }
  },
  template: `
    <div class="tweet">
      <div class="uk-card uk-card-default uk-card-body uk-width-1-1">
        <div class="tweet-card-grid">
          <div class="tweet-card-thumbnail">
            <img v-bind:src="authorThumbnailUrl">
          </div>
          <div>
            <p class="author">{{ author }} (@{{ authorScreenName }})</p>
            <p v-html="textHtml"></p>
            <a v-bind:href="tweetUrl" target="_blank">Twitterで開く</a>
          </div>
        </div>
      </div>
    </div>
  `
});

var app = new Vue({
  el: "#app",
  data: {
    playlist: null,
    tweetId: "",
    tweetText: "",
    tweetAuthor: "",
    tweetAuthorScreenName: "",
    tweetAuthorThumbnailUrl: "",
    videoUrl: "",
    videoType: ""
  },
  mounted: function() {
    this.playlist = new Playlist();
  },
  methods: {
    onSearchClicked: function(searchText) {
      this.playlist.setSearchText(searchText)
        .then(() => {
          let tweet = this.playlist.current();
          if( tweet === null ) {
            // 何も返ってこなかったとき
            alert(
              "ツイートが見つかりませんでした．\n" +
              "TwitterAPIの仕様上，1週間以上前のツイートを検索できませんのでご注意ください．");
          } else {
            this.setFromTweet(tweet);
          }
        }).catch(this.catchAPICallback);
    },
    onNextClicked: function() {
      this.playlist.next()
        .then((response) => {
          if( response === null ) {
            alert("次のツイートが見つかりませんでした");
            return;
          }
          this.setFromTweet(response);
        }).catch(this.catchAPICallback);
    },
    onPrevClicked: function() {
      this.playlist.prev()
        .then((response) => {
          if( response === null ) {
            alert("前のツイートが見つかりませんでした");
            return;
          }
          this.setFromTweet(response);
        }).catch(this.catchAPICallback);
    },
    onMusicEnded: function() {
      this.playlist.next()
        .then((response) => {
          if( response === null ) {
            alert("次のツイートが見つかりませんでした");
            return;
          }
          this.setFromTweet(response);
        }).catch(this.catchAPICallback);
    },
    setFromTweet(tweet) {
      this.tweetId = tweet["id"];
      this.tweetText = tweet["text"];
      this.tweetAuthor = tweet["author"];
      this.tweetAuthorScreenName = tweet["author_screen_name"];
      this.tweetAuthorThumbnailUrl = tweet["author_thumbnail"];
      this.videoUrl = tweet["video_url"];
      this.videoType = tweet["video_type"];
    },
    catchAPICallback: function(error) {
      console.log(error);
      if( error.response ) {
        console.log(error.response);
        let responseData = error.response.data;
        if( "error_type" in responseData ) {
          if( responseData["error_type"] === "ratelimit" ) {
            alert("Twitter検索の呼び出し回数上限に達しました．しばらく待ってから再度お試しください．");
          } else {
            alert(responseData["error"]);
          }
        } else {
          alert(responseData);
        }
      } else {
        alert(error.message);
      }
    }
  },
  computed: {
    tweetUrl: function() {
      return `https://twitter.com/${this.tweetAuthorScreenName}/status/${this.tweetId}`;
    }
  }
});
