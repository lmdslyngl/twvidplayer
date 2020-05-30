
class Playlist {
  constructor() {
    this.q = "";
    this.playlist = [];
    this.currentIndex = 0;
  }

  setSearchText(q) {
    this.q = q;
    this.currentIndex = 0;
    return this._search(q)
      .then((response) => {
        this.playlist = response;
        return Promise.resolve(this.playlist);
      });
  }

  current() {
    return this.playlist[this.currentIndex];
  }

  next() {
    if( this.playlist.length - 1 <= this.currentIndex ) {
      // プレイリストにあるより過去のツイートを参照しようとしたときは
      // 次のをツイートを検索する

      let maxId = this.playlist[this.playlist.length - 1]["id"];
      return this._search(this.q, maxId)
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
      return this._search_newer(this.q, sinceId)
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

  _search(q, maxId = -1) {
    let queryParams = { "q": q };
    if( maxId !== -1 ) {
      queryParams["max_id"] = maxId;
    }
    return axios.get("http://localhost:5000/api/search", { params: queryParams })
      .then((response) => {
        if( response.status === 200 ) {
          return Promise.resolve(response.data);
        } else {
          return Promise.reject(response.data);
        }
      });
  }

  _search_newer(q, sinceId) {
    let queryParams = { "q": q };
    if( sinceId !== -1 ) {
      queryParams["since_id"] = sinceId;
    }
    return axios.get("http://localhost:5000/api/search-newer", { params: queryParams })
      .then((response) => {
        if( response.status === 200 ) {
          return Promise.resolve(response.data);
        } else {
          return Promise.reject(response.data);
        }
      });
  }

}

