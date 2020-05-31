
class Playlist {
  constructor() {
    this.q = "";
    this.playlist = [];
    this.currentIndex = 0;
  }

  setSearchText(q) {
    this.q = q;
    this.currentIndex = 0;
    return API.search(q)
      .then((response) => {
        this.playlist = response;
        return Promise.resolve(this.playlist);
      });
  }

  current() {
    if( this.playlist.length <= this.currentIndex ) {
      return null;
    } else {
      return this.playlist[this.currentIndex];
    }
  }

  next() {
    if( this.playlist.length - 1 <= this.currentIndex ) {
      // プレイリストにあるより過去のツイートを参照しようとしたときは
      // 次のをツイートを検索する

      let maxId = this.playlist[this.playlist.length - 1]["id"];
      return API.search(this.q, maxId)
        .then((response) => {
          if( 0 < response.length ) {
            this.playlist = this.playlist.concat(response);
            this.currentIndex++;
            return Promise.resolve(this.playlist[this.currentIndex]);
          } else {
            // 何も返ってこなかったときはnullを返す
            return Promise.resolve(null);
          }
        });

    } else {
      this.currentIndex++;
      return Promise.resolve(this.playlist[this.currentIndex]);
    }

  }

  prev() {
    if( this.currentIndex <= 0 ) {
      // 最新のツイートより新しいツイートを参照しようとしたときは
      // 新しいツイートを検索する

      let sinceId = this.playlist[0]["id"];
      return API.search_newer(this.q, sinceId)
        .then((response) => {
          if( 0 < response.length ) {
            this.playlist = response.concat(this.playlist);
            this.currentIndex += response.length - 1;
            return Promise.resolve(this.playlist[this.currentIndex]);
          } else {
            // 何も返ってこなかったときはnullを返す
            return Promise.resolve(null);
          }
        });

    } else {
      this.currentIndex--;
      return Promise.resolve(this.playlist[this.currentIndex]);
    }

  }

}

