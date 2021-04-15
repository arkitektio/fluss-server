from bergen.query import DelayedGQL


GET_GRAPH = DelayedGQL("""
query Graph($id: ID!){
  graph(id: $id){
    id    
    diagram
  }
}
""")