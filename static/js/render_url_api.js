class RenderURLAPI {
    constructor(module){
        this.module = module

        return this.getURLAPI.bind(this)
    }

    getURLAPI(req){
        return "/api/"+this.module+"/"+req
    }
}

export { RenderURLAPI }