
class API {
  static search(q, maxId = -1) {
    let queryParams = { "q": q };
    if( maxId !== -1 ) {
      queryParams["max_id"] = maxId;
    }
    return axios.get("/api/search", { params: queryParams })
      .then((response) => {
        if( response.status === 200 ) {
          return Promise.resolve(response.data);
        } else {
          return Promise.reject(response.data);
        }
      }).catch((error) => {
        return Promise.reject(error);
      });
  }

  static search_newer(q, sinceId) {
    let queryParams = { "q": q };
    if( sinceId !== -1 ) {
      queryParams["since_id"] = sinceId;
    }
    return axios.get("/api/search-newer", { params: queryParams })
      .then((response) => {
        if( response.status === 200 ) {
          return Promise.resolve(response.data);
        } else {
          return Promise.reject(response.data);
        }
      }).catch((error) => {
        return Promise.reject(error);
      });
  }

  static _getRateLimitReset() {

  }

}
