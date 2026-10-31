import test from 'node:test'
import assert from 'node:assert/strict'
import {createServer} from 'vite'

test('restored atlas chapters have renderable layers and valid timeline references',async()=>{
  const server=await createServer({root:new URL('..',import.meta.url).pathname,server:{middlewareMode:true},appType:'custom'})
  try {
    const {chapters}=await server.ssrLoadModule('/src/atlas/data/index.ts')
    assert.equal(chapters.length,26)
    assert.equal(new Set(chapters.map(c=>c.id)).size,chapters.length)
    for(const chapter of chapters){
      assert.ok(chapter.title&&chapter.layers.length)
      assert.ok(chapter.view.center.every(Number.isFinite)&&Number.isFinite(chapter.view.zoom))
      const ids=new Set(chapter.layers.map(l=>l.id))
      assert.equal(ids.size,chapter.layers.length,chapter.id)
      for(const layer of chapter.layers){
        assert.equal(layer.kind,'vector',`${chapter.id}: unsupported raster`)
        assert.equal(typeof layer.data,'object',`${chapter.id}: external layer requires loading support`)
        assert.equal(layer.data.type,'FeatureCollection')
        assert.ok(layer.data.features.length)
        for(const feature of layer.data.features){
          assert.equal(feature.type,'Feature')
          assert.ok(feature.geometry)
          assert.ok(feature.geometry.coordinates.flat(Infinity).every(Number.isFinite),`${chapter.id}: invalid coordinates`)
        }
      }
      for(const event of chapter.events||[]){for(const id of [...event.showLayers||[],...event.hideLayers||[]])assert.ok(ids.has(id),`${chapter.id}: unknown timeline layer ${id}`)}
    }
  }finally{await server.close()}
})
